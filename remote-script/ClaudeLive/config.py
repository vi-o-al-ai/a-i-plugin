"""Configuration: config.json next to this package, merged over defaults.

Loading never raises. A missing or broken file yields the defaults plus a
"_config_error" entry that ClaudeLive logs once at startup.
"""
import json
import os

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILENAME = "config.json"

DEFAULTS = {
    "host": "127.0.0.1",
    "port": 9892,
    "log_level": "INFO",
    "max_requests_per_tick": 32,
    "max_tick_ms": 50,
    # Optional, undocumented in config.json (defaults are fine for Live):
    "max_line_bytes": 4 * 1024 * 1024,
    "browser_time_budget_ms": 40,
    "browser_cache_ttl_s": 60,
    "log_file": None,
}

_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")

_INT_KEYS = ("port", "max_requests_per_tick", "max_tick_ms", "max_line_bytes",
             "browser_time_budget_ms", "browser_cache_ttl_s")


def config_path():
    return os.path.join(PACKAGE_DIR, CONFIG_FILENAME)


def _coerce_int(cfg, key, minimum, errors):
    value = cfg.get(key)
    try:
        if isinstance(value, bool):
            raise TypeError("bool is not an int")
        ivalue = int(value)
    except (TypeError, ValueError):
        errors.append("%s must be an integer (got %r); using default %r" % (key, value, DEFAULTS[key]))
        cfg[key] = DEFAULTS[key]
        return
    if ivalue < minimum:
        errors.append("%s must be >= %d (got %r); using default %r" % (key, minimum, value, DEFAULTS[key]))
        cfg[key] = DEFAULTS[key]
        return
    cfg[key] = ivalue


def load_config(path=None):
    """Return the effective configuration dict. Never raises."""
    cfg = dict(DEFAULTS)
    errors = []
    if path is None:
        path = config_path()
    try:
        if os.path.exists(path):
            with open(path, "r") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                cfg.update(loaded)
            else:
                errors.append("%s must contain a JSON object; using defaults" % path)
        else:
            errors.append("%s not found; using defaults" % path)
    except Exception as exc:  # malformed JSON, permissions, ...
        errors.append("could not read %s: %s: %s; using defaults" % (path, type(exc).__name__, exc))

    _coerce_int(cfg, "port", 0, errors)
    _coerce_int(cfg, "max_requests_per_tick", 1, errors)
    _coerce_int(cfg, "max_tick_ms", 1, errors)
    _coerce_int(cfg, "max_line_bytes", 1024, errors)
    _coerce_int(cfg, "browser_time_budget_ms", 1, errors)
    _coerce_int(cfg, "browser_cache_ttl_s", 0, errors)

    host = cfg.get("host")
    if not isinstance(host, str) or host not in _LOOPBACK_HOSTS:
        errors.append("host %r is not a loopback address; forcing 127.0.0.1" % (host,))
        cfg["host"] = "127.0.0.1"

    level = cfg.get("log_level")
    if not isinstance(level, str) or level.upper() not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        errors.append("log_level %r is not valid; using INFO" % (level,))
        cfg["log_level"] = "INFO"
    else:
        cfg["log_level"] = level.upper()

    log_file = cfg.get("log_file")
    if log_file is not None and not isinstance(log_file, str):
        errors.append("log_file must be a string path or null; ignoring")
        cfg["log_file"] = None

    cfg["_config_path"] = path
    cfg["_config_error"] = "; ".join(errors) if errors else None
    return cfg
