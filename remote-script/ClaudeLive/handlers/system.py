"""sys.* handlers: ping, describe_api, log, reload_handlers."""
import os

from .. import errors, introspect, lom


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


def describe_api(ctx, params):
    path = lom.get_str(params, "path", None)
    classes = lom.get_list(params, "classes", None)
    if classes is not None:
        for item in classes:
            if not isinstance(item, str):
                raise errors.invalid_params("classes must be an array of class names", parameter="classes")
    if path is not None and not path.strip():
        path = None
    if path is not None and not os.path.isabs(path):
        path = os.path.join(introspect.PACKAGE_DIR, path)
    try:
        return introspect.describe_api(path, classes)
    except (IOError, OSError) as exc:
        raise errors.invalid_params("Cannot write API dump to %r: %s" % (path, exc), parameter="path")


def log(ctx, params):
    message = lom.get_str(params, "message")
    ctx.log_to_live("[ClaudeLive] %s" % message)
    ctx.logger.info("sys.log: %s", message)
    return {"ok": True}


def reload_handlers(ctx, params):
    """Dev convenience. Reloads lom/introspect and the handler modules, then rebuilds
    METHODS. ClaudeLive.py / server.py / dispatcher.py still need a Live restart."""
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
