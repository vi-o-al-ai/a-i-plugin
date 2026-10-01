"""sys.* handlers: ping, describe_api, log, reload_handlers."""
import os
import re

from .. import errors, introspect, lom

API_DIR_PARTS = (".claude-live", "api")
API_FILENAME = "live_api_%s.md"
MAX_LOG_CHARS = 1000
_UNSAFE_VERSION_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_DOT_RUNS = re.compile(r"\.{2,}")


def ping(ctx, params):
    version = ctx.version
    return {
        "script_version": ctx.script_version,
        "protocol_version": ctx.protocol_version,
        "live_version": version["string"],
        "live_major": version["major"],
        "live_minor": version["minor"],
        "python_version": ctx.python_version,
        "tick_count": ctx.tick_count,
    }


def api_dump_path(live_version):
    """~/.claude-live/api/live_api_<live_version>.md (the client never chooses this)."""
    safe_version = _UNSAFE_VERSION_CHARS.sub("_", str(live_version))
    safe_version = _DOT_RUNS.sub(".", safe_version).strip("._") or "unknown"
    home = os.path.expanduser("~")
    return os.path.join(home, API_DIR_PARTS[0], API_DIR_PARTS[1], API_FILENAME % safe_version)


def _make_private_dirs(path):
    """os.makedirs with mode 0o700 on every directory this call creates."""
    path = os.path.abspath(path)
    missing = []
    while path and not os.path.isdir(path):
        missing.append(path)
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    for directory in reversed(missing):
        os.mkdir(directory, 0o700)


def describe_api(ctx, params):
    if "path" in params:
        raise errors.invalid_params(
            "sys.describe_api no longer accepts 'path'; the dump is always written to "
            "~/.claude-live/api/live_api_<live_version>.md", parameter="path")
    classes = lom.get_list(params, "classes", None)
    if classes is not None:
        for item in classes:
            if not isinstance(item, str):
                raise errors.invalid_params("classes must be an array of class names", parameter="classes")
    text, count = introspect.render_api(classes)
    target = api_dump_path(ctx.version["string"])
    try:
        _make_private_dirs(os.path.dirname(target))
        written = introspect.write_dump(target, text)
    except (IOError, OSError) as exc:
        ctx.logger.warning("cannot write API dump to %s (%s); falling back to the package dir", target, exc)
        fallback = introspect.default_dump_path()
        try:
            written = introspect.write_dump(fallback, text)
        except (IOError, OSError) as exc2:
            raise errors.LiveRpcError(errors.INTERNAL_ERROR, "Cannot write the API dump to %r or %r: %s" % (
                target, fallback, exc2), {"exception": type(exc2).__name__, "detail": str(exc2)})
    return {"path": written, "classes": count, "bytes": len(text.encode("utf-8"))}


def sanitize_log_message(message):
    """One line, at most MAX_LOG_CHARS characters (Log.txt line forgery / flooding guard)."""
    message = message.replace("\r", " ").replace("\n", " ")
    if len(message) > MAX_LOG_CHARS:
        message = message[:MAX_LOG_CHARS]
    return message


def log(ctx, params):
    message = sanitize_log_message(lom.get_str(params, "message"))
    ctx.log_to_live("[ClaudeLive] %s" % message)
    ctx.logger.info("sys.log: %s", message)
    return {"ok": True}


def reload_handlers(ctx, params):
    """Dev convenience, gated by `dev_mode: true` in config.json. Reloads lom/introspect
    and the handler modules, then rebuilds METHODS. ClaudeLive.py / server.py /
    dispatcher.py still need a Live restart."""
    if ctx.config.get("dev_mode") is not True:
        # Indistinguishable from an unregistered method unless dev_mode is on.
        raise errors.LiveRpcError(errors.METHOD_NOT_FOUND, "Method 'sys.reload_handlers' does not exist",
                                  {"method": "sys.reload_handlers"})
    from .. import handlers as package
    reloaded = package.reload_handlers()
    ctx.state.clear()
    ctx.logger.info("reloaded %d modules", len(reloaded))
    return {"reloaded": reloaded, "methods": len(package.METHODS),
            "note": "ClaudeLive.py, server.py and dispatcher.py are not reloaded; restart Live for those."}


METHODS = {
    "sys.ping": ping,
    "sys.describe_api": describe_api,
    "sys.log": log,
    "sys.reload_handlers": reload_handlers,
}
