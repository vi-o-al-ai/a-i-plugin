"""Configuration: config.json next to this package, merged over defaults.

Loading never raises. A missing or broken file yields the defaults plus a
"_config_error" entry that ClaudeLive logs once at startup.

Rules (PROTOCOL.md section 4.7): `host` must be an IPv4 loopback address
(anything else, including "::1", is replaced by 127.0.0.1), `port` is 1-65535,
`dev_mode` (default false) enables sys.reload_handlers, `queue_max` bounds the
inbound request queue and `max_connections` caps concurrent clients.
"""
import ipaddress
import json
import os

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILENAME = "config.json"

DEFAULT_HOST = "127.0.0.1"

DEFAULTS = {
    "host": DEFAULT_HOST,
    "port": 9892,
    "log_level": "INFO",
    "max_requests_per_tick": 32,
    "max_tick_ms": 50,
    "dev_mode": False,
    # Optional, undocumented in config.json (defaults are fine for Live):
    "queue_max": 256,
    "max_connections": 8,
    "max_line_bytes": 4 * 1024 * 1024,
    "browser_time_budget_ms": 40,
    "browser_cache_ttl_s": 60,
    "log_file": None,
}

PORT_MIN = 1
PORT_MAX = 65535


def config_path():
    return os.path.join(PACKAGE_DIR, CONFIG_FILENAME)


def _coerce_int(cfg, key, minimum, errors, maximum=None):
    value = cfg.get(key)
    try:
        if isinstance(value, bool):
            raise TypeError("bool is not an int")
        if isinstance(value, float) and not value.is_integer():
            raise ValueError("%r is not a whole number" % (value,))
        ivalue = int(value)
    except (TypeError, ValueError):
        errors.append("%s must be an integer (got %r); using default %r" % (key, value, DEFAULTS[key]))
        cfg[key] = DEFAULTS[key]
        return
    if ivalue < minimum:
        errors.append("%s must be >= %d (got %r); using default %r" % (key, minimum, value, DEFAULTS[key]))
        cfg[key] = DEFAULTS[key]
        return
    if maximum is not None and ivalue > maximum:
        errors.append("%s must be <= %d (got %r); using default %r" % (key, maximum, value, DEFAULTS[key]))
        cfg[key] = DEFAULTS[key]
        return
    cfg[key] = ivalue


def _coerce_bool(cfg, key, errors):
    value = cfg.get(key)
    if not isinstance(value, bool):
        errors.append("%s must be true or false (got %r); using default %r" % (key, value, DEFAULTS[key]))
        cfg[key] = DEFAULTS[key]


def loopback_host(host):
    """Return the IPv4 loopback address `host` names, or None if it is not one.

    "localhost" is accepted as an alias for 127.0.0.1. "::1" (IPv6) is rejected:
    the listener is an AF_INET socket and could never bind it.
    """
    if not isinstance(host, str):
        return None
    candidate = host.strip()
    if candidate.lower() == "localhost":
        return DEFAULT_HOST
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    if address.version != 4 or not address.is_loopback:
        return None
    return str(address)


def load_config(path=None):
    """Return the effective configuration dict. Never raises."""
    cfg = dict(DEFAULTS)
    errors = []
    if path is None:
        path = config_path()
    try:
        if os.path.exists(path):
            # utf-8-sig: plain UTF-8, plus tolerance for a BOM written by Windows editors.
            with open(path, "r", encoding="utf-8-sig") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                cfg.update(loaded)
            else:
                errors.append("%s must contain a JSON object; using defaults" % path)
        else:
            errors.append("%s not found; using defaults" % path)
    except Exception as exc:  # malformed JSON, permissions, ...
        errors.append("could not read %s: %s: %s; using defaults" % (path, type(exc).__name__, exc))

    _coerce_int(cfg, "port", PORT_MIN, errors, maximum=PORT_MAX)
    _coerce_int(cfg, "max_requests_per_tick", 1, errors)
    _coerce_int(cfg, "max_tick_ms", 1, errors)
    _coerce_int(cfg, "queue_max", 1, errors)
    _coerce_int(cfg, "max_connections", 1, errors)
    _coerce_int(cfg, "max_line_bytes", 1024, errors)
    _coerce_int(cfg, "browser_time_budget_ms", 1, errors)
    _coerce_int(cfg, "browser_cache_ttl_s", 0, errors)
    _coerce_bool(cfg, "dev_mode", errors)

    host = cfg.get("host")
    resolved = loopback_host(host)
    if resolved is None:
        errors.append("host %r is not an IPv4 loopback address; forcing %s" % (host, DEFAULT_HOST))
        resolved = DEFAULT_HOST
    cfg["host"] = resolved

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
