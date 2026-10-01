"""browser.* handlers: bounded traversal with a per-root cache, and load_item."""
import time

import Live

from .. import errors, lom

CATEGORIES = ("instruments", "sounds", "drums", "audio_effects", "midi_effects", "plugins",
              "max_for_live", "packs", "user_library", "samples", "clips")
CATEGORY_TITLES = {
    "instruments": "Instruments", "sounds": "Sounds", "drums": "Drums", "audio_effects": "Audio Effects",
    "midi_effects": "MIDI Effects", "plugins": "Plug-Ins", "max_for_live": "Max for Live", "packs": "Packs",
    "user_library": "User Library", "samples": "Samples", "clips": "Clips",
}
DEFAULT_SEARCH_CATEGORIES = ("instruments", "drums", "audio_effects", "midi_effects", "sounds")
URI_HINTS = (
    ("synths", "instruments"), ("instruments", "instruments"), ("sounds", "sounds"), ("drums", "drums"),
    ("audiofx", "audio_effects"), ("midifx", "midi_effects"), ("plugins", "plugins"), ("vst", "plugins"),
    ("au:", "plugins"), ("m4l", "max_for_live"), ("maxforlive", "max_for_live"), ("packs", "packs"),
    ("userlibrary", "user_library"), ("samples", "samples"), ("clips", "clips"),
)
MAX_DEPTH = 12
FIND_CHUNK = 2000  # nodes per advance() slice while resolving a uri; the time budget is the real bound


class Entry(object):
    __slots__ = ("item", "name", "name_lower", "uri", "path", "category", "is_loadable", "is_folder", "is_device")

    def __init__(self, item, parent_path, category):
        self.item = item
        self.name = str(lom.safe_get(item, "name", ""))
        self.name_lower = self.name.strip().lower()
        uri = lom.safe_get(item, "uri")
        self.uri = str(uri) if uri is not None else None
        self.path = list(parent_path) + [self.name]
        self.category = category
        self.is_loadable = bool(lom.safe_get(item, "is_loadable", False))
        self.is_folder = bool(lom.safe_get(item, "is_folder", False))
        self.is_device = bool(lom.safe_get(item, "is_device", False))

    def to_dict(self):
        return {"name": self.name, "uri": self.uri, "category": self.category, "path": list(self.path),
                "is_loadable": self.is_loadable, "is_folder": self.is_folder, "is_device": self.is_device}


def _children(item):
    if item is None:
        return []
    try:
        return list(item.children)
    except AssertionError:
        raise
    except Exception:
        return []


class RootIndex(object):
    """Flattened, incrementally built view of one browser root."""

    def __init__(self, category, root, title):
        self.category = category
        self.title = title
        self.entries = []
        self.by_uri = {}
        self.complete = False
        self.created = time.perf_counter()
        self.stack = []
        if root is not None:
            # The root itself is addressable by uri (browser.list / browser.load) but is
            # not a search result, so it is not part of `entries`.
            root_entry = Entry(root, [], category)
            if root_entry.uri is not None:
                self.by_uri[root_entry.uri] = root_entry
        for child in reversed(_children(root)):
            self.stack.append((child, [title], 1))
        if not self.stack:
            self.complete = True

    def advance(self, deadline, max_new):
        """Visit up to max_new nodes before `deadline`; return how many were visited."""
        visited = 0
        while self.stack and visited < max_new:
            if time.perf_counter() > deadline:
                return visited
            item, parent_path, depth = self.stack.pop()
            entry = Entry(item, parent_path, self.category)
            self.entries.append(entry)
            if entry.uri is not None and entry.uri not in self.by_uri:
                self.by_uri[entry.uri] = entry
            visited += 1
            if depth < MAX_DEPTH:
                for child in reversed(_children(item)):
                    self.stack.append((child, entry.path, depth + 1))
        if not self.stack:
            self.complete = True
        return visited


def _browser(ctx):
    browser = lom.safe_get(ctx.application(), "browser")
    if browser is None:
        raise errors.unsupported("Application.browser", ctx.version["string"])
    return browser


def _root_item(ctx, category):
    return lom.safe_get(_browser(ctx), category)


def _title(ctx, category, root):
    name = lom.safe_get(root, "name") if root is not None else None
    return str(name) if name else CATEGORY_TITLES.get(category, category)


def _index_for(ctx, category):
    cache = ctx.state.setdefault("browser_index", {})
    ttl = float(ctx.config.get("browser_cache_ttl_s", 60) or 0)
    index = cache.get(category)
    if index is not None and (time.perf_counter() - index.created) > ttl:
        index = None
    if index is None:
        root = _root_item(ctx, category)
        index = RootIndex(category, root, _title(ctx, category, root))
        cache[category] = index
    return index


def _budget_s(ctx):
    return float(ctx.config.get("browser_time_budget_ms", 40) or 40) / 1000.0


def _invalidate_cache(ctx):
    ctx.state.pop("browser_index", None)


def _validate_category(name):
    if name not in CATEGORIES:
        raise errors.invalid_params("Unknown browser category %r (available: %s)" % (name, ", ".join(CATEGORIES)),
                                    parameter="categories", available=list(CATEGORIES))
    return name


def _categories(params):
    categories = lom.get_list(params, "categories", None)
    if categories is None:
        return list(DEFAULT_SEARCH_CATEGORIES)
    if not categories:
        raise errors.invalid_params("categories must not be empty", parameter="categories", available=list(CATEGORIES))
    out = []
    for item in categories:
        if not isinstance(item, str):
            raise errors.invalid_params("categories must be an array of strings", parameter="categories",
                                        available=list(CATEGORIES))
        out.append(_validate_category(item))
    return out


def _rank(name_lower, query):
    if name_lower == query:
        return 0
    if name_lower.startswith(query):
        return 1
    if query in name_lower:
        return 2
    return None


def search(ctx, params):
    query = lom.get_str(params, "query", allow_empty=False).strip().lower()
    categories = _categories(params)
    limit = lom.get_int(params, "limit", 25, minimum=1, maximum=1000)
    loadable_only = lom.get_bool(params, "loadable_only", True)
    max_nodes = lom.get_int(params, "max_nodes", 5000, minimum=1)
    deadline = time.perf_counter() + _budget_s(ctx)

    # Resumable: `visited` and `max_nodes` count only nodes traversed *in this call*;
    # entries already in the cache are always scanned for matches. `truncated` means
    # some requested category is not fully indexed yet, so the same call should be
    # repeated (the index is cached and continues where it stopped).
    visited = 0
    truncated = False
    matches = []
    for category in categories:
        index = _index_for(ctx, category)
        if not index.complete:
            if visited >= max_nodes:
                truncated = True
            else:
                visited += index.advance(deadline, max_nodes - visited)
                if not index.complete:
                    truncated = True
        for entry in index.entries:
            if loadable_only and not entry.is_loadable:
                continue
            rank = _rank(entry.name_lower, query)
            if rank is None:
                continue
            matches.append((rank, entry))
    matches.sort(key=lambda pair: pair[0])
    return {
        "items": [entry.to_dict() for _rank_value, entry in matches[:limit]],
        "truncated": truncated,
        "nodes_visited": visited,
        "total_matches": len(matches),
    }


def _ordered_categories(uri):
    lowered = (uri or "").lower()
    first = []
    for hint, category in URI_HINTS:
        if hint in lowered and category not in first:
            first.append(category)
    return first + [c for c in CATEGORIES if c not in first]


def _find_entry(ctx, uri, categories=None):
    """Resolve a browser uri through the cached per-root indexes.

    Bounded by the same per-tick budget as browser.search (PROTOCOL.md section 3,
    -32006). When the budget runs out before every candidate root is indexed, the
    progress stays cached and TIMEOUT {"retry": true} tells the client to call again.
    Returns None only when every root is fully indexed and the uri is in none of them.
    """
    deadline = time.perf_counter() + _budget_s(ctx)
    visited = 0
    for category in categories or _ordered_categories(uri):
        index = _index_for(ctx, category)
        entry = index.by_uri.get(uri)
        if entry is not None:
            return entry
        while not index.complete:
            if time.perf_counter() >= deadline:
                raise errors.LiveRpcError(
                    errors.TIMEOUT,
                    "Browser index for '%s' is still being built (%d nodes visited this call); "
                    "call again to continue resolving '%s'" % (category, visited, uri),
                    {"retry": True, "nodes_visited": visited, "category": category, "uri": uri})
            visited += index.advance(deadline, FIND_CHUNK)
            entry = index.by_uri.get(uri)
            if entry is not None:
                return entry
    return None


def list_items(ctx, params):
    category = lom.get_str(params, "category", None)
    uri = lom.get_str(params, "uri", None)
    limit = lom.get_int(params, "limit", 100, minimum=1, maximum=10000)
    if category is not None:
        _validate_category(category)
        root = _root_item(ctx, category)
        if root is None:
            raise errors.not_found("browser_item", name=category, message="Browser root %r is not available in this Live" % category)
        title = _title(ctx, category, root)
        children = [Entry(child, [title], category).to_dict() for child in _children(root)]
    elif uri is not None:
        entry = _find_entry(ctx, uri)
        if entry is None:
            raise errors.not_found("browser_item", uri=uri)
        children = [Entry(child, entry.path, entry.category).to_dict() for child in _children(entry.item)]
    else:
        children = []
        for name in CATEGORIES:
            root = _root_item(ctx, name)
            if root is None:
                continue
            title = _title(ctx, name, root)
            root_uri = lom.safe_get(root, "uri")
            children.append({"name": title, "uri": str(root_uri) if root_uri is not None else None,
                             "category": name, "path": [title], "is_loadable": False, "is_folder": True,
                             "is_device": False})
    return {"items": children[:limit], "truncated": len(children) > limit, "count": len(children)}


def load(ctx, params):
    song = ctx.song()
    uri = lom.get_str(params, "uri", allow_empty=False)
    after_path = lom.get_str(params, "after_device_path", None)
    browser = _browser(ctx)
    entry = _find_entry(ctx, uri)
    if entry is None:
        raise errors.not_found("browser_item", uri=uri)
    item = entry.item
    if not lom.safe_get(item, "is_loadable", False):
        raise errors.invalid_state("not_loadable", "Browser item '%s' (%s) is a folder and cannot be loaded" % (
            entry.name, uri), uri=uri)

    if params.get("track") is not None or params.get("track_type") == "master":
        tref = lom.track_from_params(song, params)
    else:
        selected = lom.safe_get(song.view, "selected_track")
        index, track_type = lom.track_index_of(song, selected)
        if selected is None or track_type is None:
            raise errors.invalid_state("no_selected_track", "No track is selected; pass 'track'")
        tref = lom.TrackRef(selected, index, track_type)
    track = tref.track

    after_ref = None
    if after_path is not None:
        after_ref = lom.resolve_device_path(track, after_path)
        if after_ref.is_mixer:
            raise errors.invalid_params("after_device_path cannot be 'mixer'", parameter="after_device_path")

    lom.live_set(song.view, "selected_track", track)
    before = lom.as_list(lom.safe_get(track, "devices"))
    track_view = lom.safe_get(track, "view")
    insert_modes = getattr(Live.Track, "DeviceInsertMode", None)
    restore_mode = None
    changed_mode = False
    if after_ref is not None:
        if track_view is not None:
            try:
                track_view.selected_device = after_ref.device
            except AssertionError:
                raise
            except Exception:
                pass
        select_device = lom.safe_get(song.view, "select_device")
        if select_device is not None:
            try:
                select_device(after_ref.device)
            except AssertionError:
                raise
            except Exception:
                pass
        if insert_modes is not None and track_view is not None and lom.has_attr(track_view, "device_insert_mode"):
            try:
                restore_mode = track_view.device_insert_mode
                track_view.device_insert_mode = insert_modes.selected_right
                changed_mode = True
            except AssertionError:
                raise
            except Exception:
                changed_mode = False
    try:
        lom.live_call(browser.load_item, item)
    except errors.LiveRpcError as exc:
        if exc.code == errors.LIVE_ERROR:
            # Most likely a stale BrowserItem (the browser refreshed since the index was
            # built). Drop the cache so the retry re-indexes and gets a fresh item.
            _invalidate_cache(ctx)
            data = dict(exc.data or {})
            data["retry"] = True
            raise errors.LiveRpcError(exc.code, exc.message + " (browser cache invalidated; call again)", data)
        raise
    finally:
        if changed_mode:
            # Restore whatever the user had, not blindly `default`.
            try:
                track_view.device_insert_mode = restore_mode
            except Exception:
                pass
    after = lom.as_list(lom.safe_get(track, "devices"))
    loaded = None
    for i, device in enumerate(after):
        if lom.index_of(before, device) is None:
            loaded = lom.device_summary(device, str(i))
            break
    return {
        "loaded": loaded,
        "track": lom.track_summary(song, track, tref.index, tref.track_type),
        "devices": [lom.device_summary(device, str(i)) for i, device in enumerate(after)],
        "method": "load_item",
        "item": entry.to_dict(),
    }


METHODS = {
    "browser.search": search,
    "browser.list": list_items,
    "browser.load": load,
}
