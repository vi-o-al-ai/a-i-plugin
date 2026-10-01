"""scene.* handlers."""
from .. import errors, lom


def set_scene(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "scene")
    scene = lom.resolve_scene(song, index)
    name = lom.get_str(params, "name", None)
    color_index = lom.get_color_index(params)
    has_tempo = "tempo" in params
    tempo = None
    if has_tempo and params["tempo"] is not None:
        tempo = lom.get_float(params, "tempo", minimum=20.0, maximum=999.0)

    if name is not None:
        lom.live_set(scene, "name", name)
    if color_index is not lom.MISSING:
        lom.live_set(scene, "color_index", color_index)
    if has_tempo:
        has_tempo_enabled = lom.has_attr(scene, "tempo_enabled")
        if tempo is None:
            if has_tempo_enabled:
                lom.live_set(scene, "tempo_enabled", False)
            else:
                lom.live_set(scene, "tempo", -1.0)
        else:
            lom.live_set(scene, "tempo", tempo)
            if has_tempo_enabled:
                lom.live_set(scene, "tempo_enabled", True)
    return lom.scene_summary(song, scene, index)


def fire(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "scene")
    scene = lom.resolve_scene(song, index)
    lom.live_call(scene.fire)
    return lom.scene_summary(song, scene, index)


METHODS = {
    "scene.set": set_scene,
    "scene.fire": fire,
}
