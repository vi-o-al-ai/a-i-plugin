"""Introspection of the Live module: writes a Markdown dump of classes and members.

Ground truth for debugging a Live version we could not test against. Robust to
attributes that raise on access (boost.python descriptors, deprecated props).
"""
import inspect
import os
import types

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILENAME = "live_api_dump.md"


def default_dump_path():
    return os.path.join(PACKAGE_DIR, DEFAULT_FILENAME)


def _safe_getattr(obj, name):
    try:
        return getattr(obj, name), None
    except AssertionError:
        raise
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def _doc(obj):
    try:
        doc = inspect.getdoc(obj)
    except Exception:
        doc = None
    if not doc:
        try:
            doc = getattr(obj, "__doc__", None)
        except Exception:
            doc = None
    if not doc or not isinstance(doc, str):
        return ""
    return doc.strip()


def _member_kind(obj):
    if obj is None:
        return "attribute"
    if inspect.isclass(obj):
        return "class"
    if isinstance(obj, property):
        return "property"
    if inspect.isroutine(obj) or callable(obj):
        return "method"
    type_name = type(obj).__name__
    if type_name in ("getset_descriptor", "member_descriptor", "StaticProperty", "property"):
        return "property"
    if isinstance(obj, int):
        return "enum value = %d" % int(obj)
    return "attribute (%s)" % type_name


def _iter_modules(root):
    """Yield (qualified_name, module) for a module and its sub-modules."""
    seen = set()
    stack = [(root.__name__, root)]
    while stack:
        name, module = stack.pop(0)
        if id(module) in seen:
            continue
        seen.add(id(module))
        yield name, module
        for attr in sorted(dir(module)):
            if attr.startswith("_"):
                continue
            child, _err = _safe_getattr(module, attr)
            if isinstance(child, types.ModuleType) and id(child) not in seen:
                stack.append(("%s.%s" % (name, attr), child))


def _collect_classes(module_name, module):
    classes = []
    for attr in sorted(dir(module)):
        if attr.startswith("_"):
            continue
        obj, _err = _safe_getattr(module, attr)
        if inspect.isclass(obj):
            classes.append(("%s.%s" % (module_name, attr), obj))
    return classes


def _describe_class(qualname, cls, out, depth=0):
    out.append("%s %s\n" % ("#" * min(2 + depth, 6), qualname))
    doc = _doc(cls)
    if doc:
        out.append("\n%s\n" % doc)
    out.append("\n")
    nested = []
    for member in sorted(dir(cls)):
        if member.startswith("__"):
            continue
        obj, err = _safe_getattr(cls, member)
        if err is not None:
            out.append("- `%s` — (raised on access: %s)\n" % (member, err))
            continue
        if inspect.isclass(obj) and obj is not cls:
            nested.append((member, obj))
            continue
        kind = _member_kind(obj)
        mdoc = _doc(obj) if kind != "attribute" else ""
        if mdoc and inspect.isclass(type(obj)) and mdoc == _doc(type(obj)):
            mdoc = ""
        line = "- `%s` — %s" % (member, kind)
        if mdoc:
            line += ": " + " ".join(mdoc.split())
        out.append(line + "\n")
    out.append("\n")
    for member, obj in nested:
        _describe_class("%s.%s" % (qualname, member), obj, out, depth + 1)


def describe_api(path=None, classes=None, extra_modules=None):
    """Write the Markdown dump and return {"path", "classes", "bytes"}."""
    import Live

    if path is None or not str(path).strip():
        path = default_dump_path()
    wanted = None
    if classes:
        wanted = set(str(c).lower() for c in classes)
        wanted |= set(str(c).rsplit(".", 1)[-1].lower() for c in classes)

    modules = []
    for name, module in _iter_modules(Live):
        modules.append((name, module))
    try:
        from _Framework import ControlSurface as framework_module
        modules.append(("_Framework.ControlSurface", framework_module))
    except Exception:
        pass
    for extra in extra_modules or []:
        modules.append((getattr(extra, "__name__", "module"), extra))

    out = ["# Live Python API dump\n\n"]
    count = 0
    seen = set()
    for module_name, module in modules:
        for qualname, cls in _collect_classes(module_name, module):
            if id(cls) in seen:
                continue
            seen.add(id(cls))
            short = qualname.rsplit(".", 1)[-1].lower()
            if wanted is not None and short not in wanted and qualname.lower() not in wanted:
                continue
            _describe_class(qualname, cls, out)
            count += 1
    text = "".join(out)
    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return {"path": os.path.abspath(path), "classes": count, "bytes": len(text.encode("utf-8"))}
