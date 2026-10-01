"""view.* handlers: selection and main views (UI only)."""
from .. import errors, lom

VIEW_NAMES = ("Session", "Arranger", "Detail", "Detail/Clip", "Detail/DeviceChain", "Browser")


def get_selection(ctx, params):
    return lom.selection(ctx.song())


def _show_view(ctx, name):
    app = ctx.application()
    view = lom.safe_get(app, "view")
    if view is None:
        raise errors.unsupported("Application.View", ctx.version["string"])
    lom.live_call(view.show_view, name)
    try:
        visible = bool(view.is_view_visible(name))
    except AssertionError:
        raise
    except Exception:
        visible = True
    return visible


def select(ctx, params):
    song = ctx.song()
    view = song.view
    has_track = params.get("track") is not None or params.get("track_type") == "master"
    slot_index = lom.get_int(params, "slot", None, minimum=0)
    scene_index = lom.get_int(params, "scene", None, minimum=0)
    device_path = lom.get_str(params, "device_path", None)
    show_clip = lom.get_bool(params, "show_clip_detail", False)
    show_device = lom.get_bool(params, "show_device_detail", False)

    track_ref = None
    if has_track:
        track_ref = lom.track_from_params(song, params)
    elif slot_index is not None or device_path is not None:
        raise errors.invalid_params("'track' is required when selecting a slot or a device", parameter="track")

    if scene_index is not None:
        scene = lom.resolve_scene(song, scene_index)
        lom.live_set(view, "selected_scene", scene)

    if track_ref is not None:
        lom.live_set(view, "selected_track", track_ref.track)

    slot = None
    if slot_index is not None:
        if track_ref.track_type != "track":
            raise errors.invalid_state("no_clip_slots", "%s has no clip slots" % lom.track_label(
                track_ref.track, track_ref.index, track_ref.track_type))
        slot = lom.resolve_slot(track_ref.track, slot_index)
        scenes = lom.as_list(song.scenes)
        if slot_index < len(scenes):
            lom.live_set(view, "selected_scene", scenes[slot_index])
        lom.live_set(view, "highlighted_clip_slot", slot)

    if device_path is not None:
        ref = lom.resolve_device_path(track_ref.track, device_path)
        if ref.is_mixer:
            raise errors.invalid_params("The mixer cannot be selected as a device", parameter="device_path")
        select_device = lom.safe_get(view, "select_device")
        if select_device is not None:
            lom.live_call(select_device, ref.device)
        track_view = lom.safe_get(track_ref.track, "view")
        if track_view is not None:
            try:
                track_view.selected_device = ref.device
            except AssertionError:
                raise
            except Exception:
                pass

    if show_clip:
        if slot is not None and lom.safe_get(slot, "has_clip", False):
            try:
                view.detail_clip = slot.clip
            except AssertionError:
                raise
            except Exception:
                pass
        _show_view(ctx, "Detail/Clip")
    if show_device:
        _show_view(ctx, "Detail/DeviceChain")
    return lom.selection(song)


def show_view(ctx, params):
    name = lom.get_str(params, "view")
    if name not in VIEW_NAMES:
        raise errors.invalid_params("view must be one of %s (got %r)" % (", ".join(VIEW_NAMES), name),
                                    parameter="view", available=list(VIEW_NAMES))
    visible = _show_view(ctx, name)
    return {"view": name, "visible": visible}


METHODS = {
    "view.get_selection": get_selection,
    "view.select": select,
    "view.show_view": show_view,
}
