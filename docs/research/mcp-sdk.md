# MCP Python SDK research: stdio server packaged as a `uv` project for a Claude Code plugin

Researched 2026-10-01. Everything below was verified by inspecting the installed SDK, running
experiments in the scratchpad, or reading official sources, unless explicitly marked **UNVERIFIED**.

Environment used:

| Item | Value |
| :- | :- |
| System Python | 3.11.15 (`/usr/local/bin/python3`) |
| System-installed `mcp` | **1.28.1** (`/usr/local/lib/python3.11/dist-packages/mcp`) |
| `uv` | **0.8.17** |
| Experiment venv `mcp` (what `mcp>=1.28,<2` resolves to today) | **1.30.0** |
| Latest `mcp` on PyPI | **2.2.0** (probed via `uv run --with mcp==2.2.0`) |

## TL;DR (decisions)

1. **Pin `mcp>=1.28,<2`.** `mcp` 2.x (2.0.0 released 2026-07-28, latest 2.2.0 on 2026-09-07) **removed
   `mcp.server.fastmcp`** entirely (`ModuleNotFoundError`), renamed the class to `MCPServer`, and changed error
   semantics. The 1.x line (currently 1.30.0, released the same day as 2.2.0) is the official "maintenance line"
   and the SDK's own docs say to pin `mcp>=1.28,<2`. The FastMCP `tool()` / `run()` signatures are identical in
   1.28.1 and 1.30.0.
2. **Structured output:** annotate the return type as `dict[str, Any]` (or a TypedDict / pydantic `BaseModel` /
   dataclass). A **bare `dict` annotation produces no `outputSchema` and no `structuredContent`** (verified). With a
   proper annotation the client receives **both** a JSON `TextContent` block and `structuredContent`.
3. **Errors:** `raise ToolError("msg")` becomes `CallToolResult(isError=True, content=[Text("Error executing tool
   <name>: msg")])`. Unhandled exceptions are wrapped the same way in 1.x.
4. **Logging:** stdout is the wire. 1.x does nothing to protect it (2.x does). Use
   `logging.basicConfig(stream=sys.stderr, ...)`; never `print()`.
5. **Build backend:** `uv_build` (`requires = ["uv_build>=0.8.17,<0.9.0"]`) is available in uv 0.8.17 and verified end
   to end; hatchling also verified. Either works.
6. **Launch from the plugin:** `uv run --directory <server-dir> --locked ableton-live-mcp` works from any cwd, creates
   the venv on first run, installs the project editable (source edits are picked up), and adds ~0 ms over launching
   the venv entrypoint directly once warm. `uvx --from <dir>` also works but caches a built wheel that does **not**
   pick up source edits.

---

## 1. Locally installed SDK (`mcp` 1.28.1): exact signatures and relevant source

```
$ python3 -c "import mcp, importlib.metadata as m; print(m.version('mcp'))"
1.28.1
```

Note: do not run Python with the `mcp` package directory as cwd; its `types.py` shadows the stdlib `types` module
and every import fails with a circular-import `ImportError` (hit this once during research).

### `FastMCP.__init__` (1.28.1, exact)

```
(self, name: 'str | None' = None, instructions: 'str | None' = None, website_url: 'str | None' = None,
 icons: 'list[Icon] | None' = None,
 auth_server_provider: 'OAuthAuthorizationServerProvider[Any, Any, Any] | None' = None,
 token_verifier: 'TokenVerifier | None' = None, event_store: 'EventStore | None' = None,
 retry_interval: 'int | None' = None, *,
 tools: 'list[Tool] | None' = None, debug: 'bool' = False,
 log_level: "Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']" = 'INFO',
 host: 'str' = '127.0.0.1', port: 'int' = 8000, mount_path: 'str' = '/', sse_path: 'str' = '/sse',
 message_path: 'str' = '/messages/', streamable_http_path: 'str' = '/mcp',
 json_response: 'bool' = False, stateless_http: 'bool' = False,
 warn_on_duplicate_resources: 'bool' = True, warn_on_duplicate_tools: 'bool' = True,
 warn_on_duplicate_prompts: 'bool' = True, dependencies: 'Collection[str]' = (),
 lifespan: 'Callable[[FastMCP[LifespanResultT]], AbstractAsyncContextManager[LifespanResultT]] | None' = None,
 auth: 'AuthSettings | None' = None, transport_security: 'TransportSecuritySettings | None' = None)
```

1.30.0 adds three HTTP-only keyword args after `stateless_http`: `max_request_body_size: int = 4194304`,
`session_idle_timeout: float | None = 1800`, `max_sessions: int | None = 10000`. Nothing else differs.

### `FastMCP.tool` (identical in 1.28.1 and 1.30.0, exact)

```
(self, name: 'str | None' = None, title: 'str | None' = None, description: 'str | None' = None,
 annotations: 'ToolAnnotations | None' = None, icons: 'list[Icon] | None' = None,
 meta: 'dict[str, Any] | None' = None, structured_output: 'bool | None' = None)
 -> 'Callable[[AnyFunction], AnyFunction]'
```

`FastMCP.add_tool(self, fn, name=None, title=None, description=None, annotations=None, icons=None, meta=None,
structured_output=None) -> None` takes the same options for non-decorator registration.

Docstring of `tool()` (verbatim excerpt):

> structured_output: Controls whether the tool's output is structured or unstructured
> - If None, auto-detects based on the function's return type annotation
> - If True, creates a structured tool (return type annotation permitting)
> - If False, unconditionally creates an unstructured tool

The decorator guards against `@mcp.tool` without parentheses:

```python
if callable(name):
    raise TypeError("The @tool decorator was used incorrectly. Did you forget to call it? Use @tool() instead of @tool")
```

### `FastMCP.run` / `run_stdio_async` (identical in 1.28.1 and 1.30.0)

```
run(self, transport: "Literal['stdio', 'sse', 'streamable-http']" = 'stdio', mount_path: 'str | None' = None) -> 'None'
run_stdio_async(self) -> 'None'
```

Source (1.x):

```python
def run(self, transport="stdio", mount_path=None) -> None:
    """Run the FastMCP server. Note this is a synchronous function."""
    ...
    match transport:
        case "stdio":
            anyio.run(self.run_stdio_async)
        ...

async def run_stdio_async(self) -> None:
    """Run the server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await self._mcp_server.run(read_stream, write_stream, self._mcp_server.create_initialization_options())
```

So `mcp.run()` and `mcp.run(transport="stdio")` are equivalent; `run()` is blocking and owns the event loop.

### Other decorator signatures (1.28.1)

```
FastMCP.resource(self, uri: str, *, name=None, title=None, description=None, mime_type=None, icons=None,
                 annotations: 'Annotations | None' = None, meta: 'dict[str, Any] | None' = None)
FastMCP.prompt(self, name=None, title=None, description=None, icons=None)
```

`mcp.server.fastmcp` exports: `Audio, Context, FastMCP, Icon, Image`.

### Structured-output machinery (`mcp/server/fastmcp/utilities/func_metadata.py`)

`func_metadata(...)` inspects the return annotation and calls `_try_create_model_and_schema`, which decides the
output model:

| Return annotation | Output model | Wrapped in `{"result": ...}`? |
| :- | :- | :- |
| `None` | wrapped model | yes |
| `dict[str, T]` (GenericAlias, str keys) | `RootModel`-style dict model (`additionalProperties: true` for `Any`) | no |
| other generics (`list[str]`, `dict[int, X]`, `X \| None`, `tuple`...) | wrapped model | yes |
| `BaseModel` subclass | the model itself | no |
| `TypedDict` | model built from the TypedDict | no |
| `str`, `int`, `float`, `bool`, `bytes` | wrapped model | yes |
| any other class **with** type hints (dataclass, annotated class) | model built from `get_type_hints()` | no |
| class **without** type hints, **bare `dict`**, **no annotation** | none -> unstructured | n/a |

The bare `dict` case: `dict` is a `type`, not a `GenericAlias`, so it falls into "other class types";
`get_type_hints(dict)` is empty, so `model` stays `None` and the tool is unstructured. Verified in the experiment.

`FuncMetadata.convert_result` (verbatim core):

```python
if isinstance(result, CallToolResult):
    ...validate structuredContent against output_model if any...
    return result
unstructured_content = _convert_to_content(result)
if self.output_schema is None:
    return unstructured_content
else:
    if self.wrap_output:
        result = {"result": result}
    validated = self.output_model.model_validate(result)
    structured_content = validated.model_dump(mode="json", by_alias=True)
    return (unstructured_content, structured_content)
```

`_convert_to_content` turns non-`str` results into `TextContent(text=pydantic_core.to_json(result, fallback=str,
indent=2))`; `str` is passed through; lists are flattened to one content block per item; `Image`/`Audio`/`ContentBlock`
are passed through.

The low-level handler (`mcp/server/lowlevel/server.py`, `Server.call_tool`) then builds the `CallToolResult`: a
`(unstructured, structured)` tuple goes to `content` + `structuredContent`; a plain `dict` from a low-level handler is
put in `structuredContent` with `json.dumps(results, indent=2)` as text; if the tool advertises `outputSchema`, the
structured content is validated with `jsonschema` and a failure becomes an `isError` result
(`"Output validation error: ..."`). Any exception in the handler becomes `self._make_error_result(str(e))`.

### Error handling (`mcp/server/fastmcp/tools/base.py`, `Tool.run`)

```python
try:
    result = await self.fn_metadata.call_fn_with_arg_validation(...)
    if convert_result:
        result = self.fn_metadata.convert_result(result)
    return result
except UrlElicitationRequiredError:
    raise
except Exception as e:
    raise ToolError(f"Error executing tool {self.name}: {e}") from e
```

So in 1.x **every** exception (including `ToolError`) is re-raised as `ToolError("Error executing tool <name>: <msg>")`,
which the low-level handler turns into `CallToolResult(isError=True, content=[TextContent(text=...)])`.

`mcp/server/fastmcp/exceptions.py` (verbatim):

```python
class FastMCPError(Exception): """Base error for FastMCP."""
class ValidationError(FastMCPError): """Error in validating parameters or return values."""
class ResourceError(FastMCPError): """Error in resource operations."""
class ToolError(FastMCPError): """Error in tool operations."""
class InvalidSignature(Exception): """Invalid signature for use with FastMCP."""
```

Import path: `from mcp.server.fastmcp.exceptions import ToolError`.

### `Context` (1.28.1 == 1.30.0)

Public API (pydantic model; relevant members):

```
ctx.request_id            property
ctx.client_id             property
ctx.fastmcp               property  -> the FastMCP instance (ctx.fastmcp.instructions, .name, .settings)
ctx.session               property  -> ServerSession
ctx.request_context       property  -> RequestContext (.lifespan_context, .meta, .request_id)
await ctx.debug/info/warning/error(message: str, **extra: Any) -> None
await ctx.log(level: Literal['debug','info','warning','error'], message: str, *, logger_name: str | None = None) -> None
await ctx.report_progress(progress: float, total: float | None = None, message: str | None = None) -> None
await ctx.read_resource(uri: str | AnyUrl) -> Iterable[ReadResourceContents]
await ctx.elicit(message: str, schema: type[ElicitSchemaModelT]) -> ElicitationResult
```

`ctx.info()` sends a `notifications/message` to the **client** (`session.send_log_message(level, data=message,
logger=logger_name, related_request_id=self.request_id)`). It does not write to stderr. Context injection: any
parameter annotated `Context` (any name) is filled; `FastMCP.get_context()` notes it is "only valid during a request".

### `ToolAnnotations`, `Tool`, `CallToolResult` (`mcp/types.py`)

```
ToolAnnotations: title: str | None, readOnlyHint: bool | None, destructiveHint: bool | None,
                 idempotentHint: bool | None, openWorldHint: bool | None   (all default None)
Tool: name: str, title: str | None, description: str | None, inputSchema: dict, outputSchema: dict | None,
      icons: list[Icon] | None, annotations: ToolAnnotations | None, meta: dict | None (wire name `_meta`),
      execution: ToolExecution | None
CallToolResult: meta: dict | None, content: list[TextContent|ImageContent|AudioContent|ResourceLink|EmbeddedResource],
                structuredContent: dict | None, isError: bool = False
```

`FastMCP.list_tools()` maps `title`, `annotations`, `icons`, `_meta=info.meta` and `outputSchema=info.output_schema`.

### Lifespan wiring

`FastMCP(lifespan=...)` wraps your `@asynccontextmanager async def lifespan(server: FastMCP) -> AsyncIterator[T]`
via `lifespan_wrapper` and passes it to the low-level `Server`. The yielded value is available in tools as
`ctx.request_context.lifespan_context`. Verified: startup log printed before `initialize` completed, shutdown log on
client disconnect.

---

## 2. Latest version on PyPI and API drift

From `https://pypi.org/pypi/mcp/json` (fetched 2026-10-01):

| Version | Upload time (UTC) | Line |
| :- | :- | :- |
| 1.28.0 | 2026-06-16 21:37 | 1.x |
| 1.28.1 (installed) | 2026-06-26 12:57 | 1.x |
| 2.0.0b1 / b2 / rc1 | 2026-06-30 / 07-14 / 07-27 | 2.x pre |
| 1.29.0 | 2026-07-28 13:41 | 1.x |
| 2.0.0 | 2026-07-28 13:45 | 2.x stable |
| 1.29.1 | 2026-08-24 18:30 | 1.x |
| 2.1.0 / 2.1.1 / 2.0.1 | 2026-08-24 / 08-25 / 08-26 | 2.x |
| 1.30.0 | 2026-09-07 14:34 | 1.x |
| **2.2.0 (latest)** | **2026-09-07 16:06** | 2.x |

`requires_python` for 2.2.0: `>=3.10`. (A WebFetch summary of the GitHub releases page rendered the years as 2024;
the PyPI upload timestamps above are authoritative.)

### 1.28.1 -> 1.30.0 (safe within `>=1.28,<2`)

- 1.29.0 (release notes): "Route Context.report_progress() to the originating request stream", "Add Streamable HTTP
  request body limits", "reject trailing newline in tool-name validation", "Move the v1.x docs to /v1/ and mark v1.x
  as the maintenance line". No FastMCP tool/structured-output/stdio changes.
- 1.30.0: HTTP redirect restrictions, idle HTTP session expiry (30 min) and 10,000-session cap, OAuth issuer
  validation; new `session_idle_timeout=` / `max_sessions=` on FastMCP; two OAuth deprecation warnings. No
  structured-output, tool or stdio changes.
- Verified by signature diff: `tool()`, `run()`, `Context.info/log`, `ToolAnnotations` unchanged.

### 1.x -> 2.x (why we pin `<2`)

Verified empirically with `uv run --no-project --with "mcp==2.2.0"`:

```
import mcp.server.fastmcp FAILED: ModuleNotFoundError No module named 'mcp.server.fastmcp'. This is mcp 2.x, where
FastMCP was renamed to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed; see the
migration guide at https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver or pin
'mcp<2' to keep running v1 code.
```

- `from mcp.server import MCPServer` / `from mcp.server.mcpserver import MCPServer, Context`.
- `MCPServer.__init__(self, name=None, title=None, description=None, instructions=None, website_url=None, icons=None,
  version='', auth_server_provider=None, token_verifier=None, *, tools=None, resources=None, extensions=None,
  debug=False, log_level='INFO', warn_on_duplicate_*=True, dependencies=None, lifespan=None, auth=None,
  resource_security=..., request_state_security=None, cache_hints=None, subscriptions=None, middleware=None)` --
  HTTP settings moved out of the constructor.
- `MCPServer.tool(...)` has the **same** signature as 1.x `FastMCP.tool`.
- `MCPServer.run(self, transport='stdio', **kwargs)`.
- `ToolError` moved to `mcp.server.mcpserver.exceptions`; `mcp.server.exceptions` does not exist.
- `Context.info(self, data: Any, *, logger_name=None)` (was `message: str, **extra`).
- Error semantics (v2 "What's new"): "an exception is a protocol error, never an is_error=True tool result" ... "only a
  ToolError's message reaches the model: any other exception now reads Error executing tool <name>, with the traceback
  in your server log." (2.1.0 notes: ToolError/ResourceError logged at INFO without traceback; unexpected exceptions
  logged at ERROR with traceback.)
- 2.1.0: tools annotated to return content blocks (`TextContent`, `Image`, ...) "no longer advertise `outputSchema` or
  return `structuredContent`"; pass `structured_output=True` to keep the old shape. dict/pydantic returns still
  structured.
- 2.0.0rc1+: `stdio_server()` "serves from private duplicates of stdin/stdout and points fd 0 at the null device and fd 1
  at stderr while it runs" (confirmed in 2.2.0 source: `_claim_fd(1, sys.stdout, ...)`, restored on exit).
- `Client` object replaces `stdio_client` + `ClientSession` + `initialize()` (v1-style client imports still import in
  2.2.0, verified).
- Migration guide: "If your package depends on `mcp`, keep a `<2` upper bound until you've migrated." What's-new page:
  "v1.x is not going anywhere. It moves to maintenance, keeps getting critical fixes and security patches." ...
  "keep an upper bound (for example mcp>=1.28,<2)". The v1 docs index says: "Pin `mcp<2` (for example `mcp>=1.28,<2`)
  so an unpinned install doesn't move you to 2.x."

---

## 3. Official docs (quoted)

The `main` README is now the **v2** README (126 lines; docs at <https://py.sdk.modelcontextprotocol.io/>, v1 docs
at <https://py.sdk.modelcontextprotocol.io/v1/>). Its "A server in 15 lines" uses `from mcp.server import MCPServer`
and `uv add "mcp[cli]"` (the `cli` extra adds the `mcp dev`/`mcp run`/`mcp install` CLI; not needed at runtime).

For 1.x I used the README and `docs/server.md` / `docs/testing.md` at tag `v1.28.1`
(`https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v1.28.1/...`).

### FastMCP quickstart (v1.28.1 README, verbatim)

```python
"""
FastMCP quickstart example.

Run from the repository root:
    uv run examples/snippets/servers/fastmcp_quickstart.py
"""

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo", json_response=True)


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### stdio run pattern (docs/server.md "Direct Execution", verbatim)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")


@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


def main():
    """Entry point for the direct execution server."""
    mcp.run()


if __name__ == "__main__":
    main()
```

The docs show it run as `uv run direct-execution-server` (a `[project.scripts]` entry) or `python servers/direct_execution.py`.
`mcp.run()` defaults to `transport="stdio"` (signature above). Also: "Note that `uv run mcp run` or `uv run mcp dev`
only supports server using FastMCP and not the low-level server variant."

### Lifespan (docs/server.md "Server", verbatim)

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession


# Mock database class for example
class Database:
    @classmethod
    async def connect(cls) -> "Database":
        return cls()

    async def disconnect(self) -> None:
        pass

    def query(self) -> str:
        return "Query result"


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    db: Database


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    # Initialize on startup
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        # Cleanup on shutdown
        await db.disconnect()


# Pass lifespan to server
mcp = FastMCP("My App", lifespan=app_lifespan)


# Access type-safe lifespan context in tools
@mcp.tool()
def query_db(ctx: Context[ServerSession, AppContext]) -> str:
    """Tool that uses initialized resources."""
    db = ctx.request_context.lifespan_context.db
    return db.query()
```

### Structured output (docs/server.md, verbatim prose)

> Tools will return structured results by default, if their return type annotation is compatible. Otherwise, they
> will return unstructured results.
>
> Structured output supports these return types:
> - Pydantic models (BaseModel subclasses)
> - TypedDicts
> - Dataclasses and other classes with type hints
> - `dict[str, T]` (where T is any JSON-serializable type)
> - Primitive types (str, int, float, bool, bytes, None) - wrapped in `{"result": value}`
> - Generic types (list, tuple, Union, Optional, etc.) - wrapped in `{"result": value}`
>
> Classes without type hints cannot be serialized for structured output. Only classes with properly annotated
> attributes will be converted to Pydantic models for schema generation and validation.
>
> Structured results are automatically validated against the output schema generated from the annotation. ...
>
> **Note:** For backward compatibility, unstructured results are also returned. ...
>
> **Note:** In cases where a tool function's return type annotation causes the tool to be classified as structured
> _and this is undesirable_, the classification can be suppressed by passing `structured_output=False` to the `@tool`
> decorator.

The docs' snippet uses `-> dict[str, float]`, `-> WeatherData` (BaseModel), `-> LocationInfo` (TypedDict),
`-> list[str]` (returns `{"result": [...]}`), `-> float` (returns `{"result": 22.5}`). Note the docs never show a bare
`dict`; see section 4 for why that matters.

**Does returning a `dict` produce both text and `structuredContent`?** Yes, when the annotation is `dict[str, T]`
(verified below: `content=[TextContent(JSON)]` plus `structuredContent`). With a bare `dict` or no annotation you only
get the JSON text block.

For full control (including `_meta` hidden from the model) a tool may return `CallToolResult` directly; the docs note
"`CallToolResult` must always be returned (no `Optional` or `Union`). For empty results, use `CallToolResult(content=[])`."

### ToolError (docs/server.md "Error Handling", verbatim)

> The MCP protocol uses the `isError` flag on `CallToolResult` to distinguish error responses from successful ones.
> There are three ways to handle errors:

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import CallToolResult, TextContent

mcp = FastMCP("Tool Error Handling Example")


# Option 1: Raise ToolError for expected error conditions.
# The error message is returned to the client with isError=True.
@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ToolError("Cannot divide by zero")
    return a / b


# Option 2: Unhandled exceptions are automatically caught and
# converted to error responses with isError=True.
@mcp.tool()
def read_config(path: str) -> str:
    """Read a configuration file."""
    # If this raises FileNotFoundError, the client receives an
    # error response like "Error executing tool read_config: ..."
    with open(path) as f:
        return f.read()


# Option 3: Return CallToolResult directly for full control
# over error responses, including custom content.
@mcp.tool()
def validate_input(data: str) -> CallToolResult:
    ...
        return CallToolResult(content=[TextContent(type="text", text="\n".join(errors))], isError=True)
```

> - **`ToolError`** is the preferred approach for most cases -- raise it with a descriptive message and the framework
>   handles the rest.
> - **Unhandled exceptions** are caught automatically, so tools won't crash the server. The exception message is
>   forwarded to the client as an error response.

### Context injection and `ctx.info` (docs/server.md, verbatim)

> The Context object is automatically injected into tool and resource functions that request it via type hints.

```python
@mcp.tool()
async def long_running_task(task_name: str, ctx: Context[ServerSession, None], steps: int = 5) -> str:
    """Execute a task with progress updates."""
    await ctx.info(f"Starting: {task_name}")
    for i in range(steps):
        progress = (i + 1) / steps
        await ctx.report_progress(progress=progress, total=1.0, message=f"Step {i + 1}/{steps}")
        await ctx.debug(f"Completed step {i + 1}")
    return f"Task '{task_name}' completed"
```

> - `await ctx.debug(message)` - Send debug log message
> - `await ctx.info(message)` - Send info log message
> - `await ctx.warning(message)` - Send warning log message
> - `await ctx.error(message)` - Send error log message
> - `await ctx.log(level, message, logger_name=None)` - Send log with custom level
> - `ctx.fastmcp.instructions` - Server instructions/description provided to clients

The plain `Context` annotation works too ("The context parameter can have any name as long as it's type-annotated").

### Tool annotations

`docs/server.md` at v1.28.1 **does not document tool annotations** (grep for "annotation" finds only type-annotation
prose). The API is in the source: `@mcp.tool(annotations=ToolAnnotations(readOnlyHint=..., destructiveHint=...,
idempotentHint=..., openWorldHint=..., title=...))` with `from mcp.types import ToolAnnotations`. Verified in section 4
that they are emitted on the wire in `tools/list`.

---

## 4. Experiment (scratchpad, left in place)

Location: `/tmp/claude-0/-home-user-a-i-plugin/1a146770-21a9-5163-b278-14fae6ba0f84/scratchpad/`

- `ableton-live-mcp/` -- the uv project (final state uses `uv_build`; `pyproject.hatchling.toml` beside it is the
  hatchling variant that was also verified).
- `client_probe.py`, `client_probe2.py` -- stdio clients (`mcp.client.stdio`); `bad_server.py` / `bad_client.py` --
  stdout-corruption test; `v2probe/` -- 2.2.0 probe; `uvbuild-probe/` -- `uv init --build-backend uv` output;
  downloaded docs (`README-*.md`, `v1-docs-*.md`, `spec-transports-*.mdx`, `uv-python-versions.md`).

### pyproject.toml (verified, hatchling variant)

```toml
[project]
name = "ableton-live-mcp"
version = "0.1.0"
description = "Experimental MCP server (stdio) for a Claude Code plugin"
requires-python = ">=3.11"
dependencies = ["mcp>=1.28,<2"]

[project.scripts]
ableton-live-mcp = "ableton_live_mcp:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ableton_live_mcp"]

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

`uv sync` (deps already in uv cache): **1.4 s** wall; lock resolved `mcp==1.30.0`, `pydantic==2.13.5`, `pytest==9.1.1`,
`pytest-asyncio==1.4.0`, `anyio`, `starlette==1.7.0`, `uvicorn`, `jsonschema`, ... (36 packages).

### `uv_build` variant (verified: `uv sync`, round trip, `uv run pytest`, `uv build` all pass)

```toml
[build-system]
requires = ["uv_build>=0.8.17,<0.9.0"]
build-backend = "uv_build"
```

(No `[tool.*]` section needed; `uv_build` expects `src/<module_name>/__init__.py` where the module name is the project
name with `-` -> `_`. `uv init --build-backend uv --package` in uv 0.8.17 generates exactly this pin.) `uv build`
produced `ableton_live_mcp-0.1.0-py3-none-any.whl` and the sdist.

### Server module (abridged; the full file is in the scratchpad)

```python
import logging, sys
from typing import Any, TypedDict
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

mcp = FastMCP("ableton-live-mcp", instructions="Experimental server. Use get_song_info to read state.", lifespan=lifespan)

@mcp.tool(title="Get song info",
          annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
          meta={"category": "song"})
async def get_song_info(ctx: Context) -> dict[str, Any]:
    await ctx.info("get_song_info called")
    state: AppState = ctx.request_context.lifespan_context
    return {"tempo": 120.0, "tracks": 3, "connected": state.connected}

@mcp.tool()
def fail_tool(reason: str) -> str:
    raise ToolError(f"failed on purpose: {reason}")

def main() -> None:
    mcp.run(transport="stdio")
```

### (b) stdio round trip: exact client output

Client: `StdioServerParameters(command="uv", args=["run", "ableton-live-mcp"])` -> `stdio_client` -> `ClientSession`
-> `initialize()` -> `list_tools()` -> `call_tool()`.

`initialize()` result: `serverInfo = {'name': 'ableton-live-mcp', 'version': '1.30.0'}` (version is the SDK version,
not the package version, in 1.x), `instructions = 'Experimental server. Use get_song_info to read state.'`.

`tools/list` entry for `get_song_info` (title, annotations and meta all on the wire):

```json
{
 "name": "get_song_info",
 "title": "Get song info",
 "description": "Return basic song info as dict[str, Any] (structured output).",
 "inputSchema": {"properties": {}, "title": "get_song_infoArguments", "type": "object"},
 "outputSchema": {"additionalProperties": true, "title": "get_song_infoDictOutput", "type": "object"},
 "annotations": {"readOnlyHint": true, "destructiveHint": false, "idempotentHint": true, "openWorldHint": false},
 "meta": {"category": "song"}
}
```

`call_tool` results (exact `model_dump(exclude_none=True)` JSON):

| Tool return annotation | `outputSchema` advertised | `call_tool` result |
| :- | :- | :- |
| `-> dict[str, Any]` | `{"additionalProperties": true, "title": "get_song_infoDictOutput", "type": "object"}` | `{"content": [{"type": "text", "text": "{\n  \"tempo\": 120.0,\n  \"tracks\": 3,\n  \"connected\": true\n}"}], "structuredContent": {"tempo": 120.0, "tracks": 3, "connected": true}, "isError": false}` |
| `-> dict` (bare) | **none** | `{"content": [{"type": "text", "text": "{\n  \"tempo\": 120.0\n}"}], "isError": false}` -- **no structuredContent** |
| `-> SongInfoTD` (TypedDict) | `{"properties": {"tempo": {"title": "Tempo", "type": "number"}, "tracks": {...}}, "required": ["tempo", "tracks"], "title": "SongInfoTD", "type": "object"}` | text JSON + `"structuredContent": {"tempo": 120.0, "tracks": 3}` |
| `-> SongInfoModel` (BaseModel) | same shape, title `SongInfoModel` | text JSON + `"structuredContent": {"tempo": 120.0, "tracks": 3}` |
| `-> SongInfoDC` (dataclass) | same shape, title `SongInfoDC` | text JSON + `"structuredContent": {"tempo": 120.0, "tracks": 3}` |
| `-> list[str]` | `{"properties": {"result": {"items": {"type": "string"}, "type": "array", ...}}, "required": ["result"], "title": "str_listOutput", ...}` | `{"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}], "structuredContent": {"result": ["a", "b"]}, "isError": false}` |
| `-> str` | `{"properties": {"result": {"title": "Result", "type": "string"}}, "required": ["result"], "title": "plain_textOutput", "type": "object"}` | `{"content": [{"type": "text", "text": "x=5"}], "structuredContent": {"result": "x=5"}, "isError": false}` |
| no annotation | none | text JSON only |
| `-> dict[str, Any]` with `structured_output=False` | none | text JSON only |
| `raise ToolError("failed on purpose: demo")` | (n/a) | `{"content": [{"type": "text", "text": "Error executing tool fail_tool: failed on purpose: demo"}], "isError": true}` |
| `raise RuntimeError("unexpected crash")` | (n/a) | `{"content": [{"type": "text", "text": "Error executing tool crash_tool: unexpected crash"}], "isError": true}` |

Server stderr during the run (forwarded by `stdio_client`): `INFO ableton_live_mcp: lifespan: startup`,
`INFO mcp.server.lowlevel.server: Processing request of type ListToolsRequest`, `... CallToolRequest` (x N),
`INFO ableton_live_mcp: lifespan: shutdown`. The `ctx.info(...)` message went to the client as a logging notification
(ignored by the probe's default `logging_callback`), not to stderr.

### (c) launching from another cwd, and timings

All runs from `cwd=/tmp`, client = system Python with `mcp` 1.28.1, server venv `mcp` 1.30.0. "initialize" is the
time from subprocess spawn to `initialize()` returning; "total" is the whole probe session (init + list_tools + 5 calls);
"wall" includes the client's own Python start-up.

| Launch command | initialize | total | wall | Notes |
| :- | :- | :- | :- | :- |
| `uv run ableton-live-mcp` (cwd = project), 1st | 0.48 s | 0.58 s | 1.07 s | venv already synced |
| same, 2nd | 0.44 s | 0.53 s | 1.02 s | |
| `uv run --directory <dir> ableton-live-mcp`, 1st | 0.44 s | 0.53 s | 0.98 s | works from any cwd |
| same, 2nd | 0.51 s | 0.60 s | 1.06 s | |
| `rm -rf .venv` then `uv run --directory <dir> --locked ableton-live-mcp` | **0.92 s** | 1.01 s | 1.50 s | uv printed `Creating virtual environment at: .venv` / `Installed 36 packages in 8ms` (wheels already in uv cache) |
| same, warm | 0.44 s | 0.51 s | 0.98 s | |
| `uv cache clean ableton-live-mcp` then `uvx --from <dir> ableton-live-mcp` | 0.47 s | 0.56 s | 1.00 s | rebuilt the wheel; deps cached |
| `uvx --from <dir> ableton-live-mcp`, warm | 0.44 s | 0.53 s | 0.97 s | |
| `<dir>/.venv/bin/ableton-live-mcp` directly | 0.46 s | 0.55 s | 1.02 s | uv adds ~0 overhead when warm; the ~0.45 s is Python importing mcp/pydantic/starlette |
| `uvx --from <dir> ableton-live-mcp --help` after first-ever build | -- | -- | 1.375 s | includes `Building ableton-live-mcp` |

Findings:

- `uv run --directory <dir> ableton-live-mcp` **works from another cwd** (also `uv --directory <dir> run ...`).
  It auto-creates/syncs `.venv` on first launch; `--locked` asserts `uv.lock` is current (fails instead of
  re-resolving); `--frozen` skips lock checks entirely.
- `uvx --from <dir> ableton-live-mcp` **works** too, but (1) the very first attempt in this sandbox failed with
  `error: Failed to fetch ... pydantic_core ... client error (Connect)` because `uvx` re-resolves from PyPI and ignores
  `uv.lock`; a retry succeeded. (2) After editing `src/.../__init__.py` (no pyproject change) `uvx --from` **still ran
  the old code** (stale cached wheel), while `uv run --directory` picked the edit up immediately (editable install).
  `uvx --reinstall` / `--refresh` could not be verified here (both hit the same transient PyPI connect error): UNVERIFIED.
- A true cold start on a machine with an empty uv cache (download ~36 wheels, possibly download a managed Python) was
  not measurable here: UNVERIFIED, expect several seconds to tens of seconds depending on network.

### Tests

`tests/test_server.py` uses the in-memory transport and passes (`uv run pytest -q` -> `3 passed in 0.38s`, ~1.0 s wall):

```python
from mcp.shared.memory import create_connected_server_and_client_session as client_session
from ableton_live_mcp import mcp

async def test_get_song_info_structured():
    async with client_session(mcp._mcp_server) as client:
        res = await client.call_tool("get_song_info", {})
    assert res.isError is False
    assert res.structuredContent == {"tempo": 120.0, "tracks": 3, "connected": True}

async def test_tool_error_is_error_result():
    async with client_session(mcp._mcp_server) as client:
        res = await client.call_tool("fail_tool", {"reason": "x"})
    assert res.isError is True
    assert "failed on purpose: x" in res.content[0].text
```

`create_connected_server_and_client_session(server: Server | FastMCP, read_timeout_seconds=None, sampling_callback=None,
list_roots_callback=None, logging_callback=None, message_handler=None, client_info=None, raise_exceptions=False,
elicitation_callback=None) -> AsyncGenerator[ClientSession, None]` (same in 1.28.1 and 1.30.0; accepts the `FastMCP`
instance directly too).

---

## 5. Logging: stdout is the protocol channel

MCP specification (2025-06-18, `basic/transports`, "stdio", verbatim):

> - The server reads JSON-RPC messages from its standard input (`stdin`) and sends messages to its standard output
>   (`stdout`).
> - Messages are delimited by newlines, and **MUST NOT** contain embedded newlines.
> - The server **MAY** write UTF-8 strings to its standard error (`stderr`) for logging purposes. Clients **MAY**
>   capture, forward, or ignore this logging.
> - The server **MUST NOT** write anything to its `stdout` that is not a valid MCP message.

What the SDK does:

- **1.x `stdio_server()`** wraps `sys.stdin.buffer` / `sys.stdout.buffer` as UTF-8 text streams and writes
  `model_dump_json(by_alias=True, exclude_none=True) + "\n"` per message. It does **not** redirect fd 1, so any
  `print()` in your code (or a library's) goes straight onto the wire (verified from source; `'dup' in source` is False).
- **2.x `stdio_server()`** claims fd 0/1 and points fd 1 at stderr while serving ("stray output misses the wire").
  Not available to us under the `<2` pin.
- `FastMCP.__init__` calls `configure_logging(self.settings.log_level)`, which does `logging.basicConfig(level=...,
  format="%(message)s", handlers=[RichHandler(console=Console(stderr=True))])` when `rich` is importable, else
  `logging.StreamHandler()` whose default stream is `sys.stderr`. So the SDK's own logging already targets stderr;
  `rich` is not installed by plain `mcp` (it comes with `mcp[cli]`).
- Experiment: a server that `print()`s a non-JSON line before `mcp.run()` and inside a tool was still usable from the
  **Python** `stdio_client` ("initialized OK", `ping -> pong`), because the client forwards JSON-parse failures as an
  `Exception` object to `ClientSession._default_message_handler`, which only does `await anyio.lowlevel.checkpoint()`
  (silently drops it). Other clients are not that forgiving; how Claude Code's client reacts to a stray line is
  **UNVERIFIED**. Follow the spec and never write to stdout.

Recommended pattern (verified in the experiment; call it once at import time of the server module):

```python
import logging, sys

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# the low-level server logs "Processing request of type ..." at INFO for every request; quieten it if noisy:
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
log = logging.getLogger("ableton_live_mcp")
```

Because `FastMCP(...)` also calls `logging.basicConfig(...)`, whichever runs first wins (basicConfig is a no-op once
the root logger has handlers). Both target stderr, so ordering only affects the format. Optionally write to a file
with `logging.FileHandler(...)` as well. Use `await ctx.info(...)` for messages that should reach the **client** as MCP
log notifications; use the `logging` module for operator-facing stderr logs.

---

## 6. Recommendations

- **Dependency pin:** `dependencies = ["mcp>=1.28,<2"]`. Installed major.minor is 1.28; the next major (2.0) breaks the
  import path. Today this resolves to 1.30.0, whose FastMCP decorator/run API is identical to 1.28.1. Re-evaluate a 2.x
  migration later (rename to `MCPServer`, `ToolError` import path, `Context.info(data)`, error semantics).
- **Build backend:** `uv_build` with `requires = ["uv_build>=0.8.17,<0.9.0"]` (verified; zero extra config; exactly what
  `uv init --build-backend uv` writes in 0.8.17). Hatchling is the portable fallback (verified; needs
  `[tool.hatch.build.targets.wheel] packages = ["src/ableton_live_mcp"]`). Both work with `uv run`'s editable install.
- **Tests:** `uv run pytest` (uv syncs the default `dev` dependency group automatically; `uv run --no-dev` to skip).
  Add `[dependency-groups] dev = ["pytest>=8", "pytest-asyncio>=0.24"]` and `[tool.pytest.ini_options]
  asyncio_mode = "auto"` (verified: pytest 9.1.1 + pytest-asyncio 1.4.0). Alternative without pytest-asyncio: the
  official `docs/testing.md` uses anyio's pytest plugin (`@pytest.mark.anyio` plus an `anyio_backend` fixture returning
  `"asyncio"`); anyio is already a transitive dependency of `mcp`. The in-memory
  `create_connected_server_and_client_session` avoids spawning a subprocess.
- **Python on macOS:** `requires-python = ">=3.11"`. uv docs (0.8.17, `docs/concepts/python-versions.md`): "By default, uv
  will automatically download Python versions if they cannot be found on the system." and "uv bundles a list of
  downloadable CPython and PyPy distributions for macOS, Linux, and Windows." Downloads can be disabled with
  `python-downloads = "manual"` / `--no-python-downloads` / `UV_PYTHON_DOWNLOADS=never`. uv discovers "A Python
  interpreter on the `PATH` as `python`, `python3`, or `python3.x` on macOS and Linux" (so Homebrew Python is used if
  present; otherwise a `python-build-standalone` build is fetched to `~/.local/share/uv/python/`). `uv python list` on
  this box shows `<download available>` entries for 3.11/3.12/3.13. The stock macOS `/usr/bin/python3` version is
  **UNVERIFIED** here (commonly 3.9.x via Xcode CLT), so assume uv will download a managed interpreter on a clean Mac;
  budget that into first-launch time. Optionally commit a `.python-version` (uv honours it) to make the choice explicit.
- **Claude Code plugin wiring** (from the plugin reference at code.claude.com): the plugin's MCP servers live in
  `.mcp.json` at the plugin root (or inline under `mcpServers` in `.claude-plugin/plugin.json`); for stdio servers
  `${CLAUDE_PLUGIN_ROOT}` resolves in `command`, `args`, `env`, and `CLAUDE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_DATA` are
  exported to the server process. `${CLAUDE_PLUGIN_ROOT}` "changes when the plugin updates, so don't write state there";
  `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/<id>/`) is "for installed dependencies such as `node_modules`,
  generated code, and caches". Suggested entry (UNVERIFIED end-to-end inside Claude Code; each piece verified separately):

  ```json
  {
    "mcpServers": {
      "ableton-live": {
        "command": "uv",
        "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}/server", "--locked", "ableton-live-mcp"],
        "env": { "UV_PROJECT_ENVIRONMENT": "${CLAUDE_PLUGIN_DATA}/venv" }
      }
    }
  }
  ```

  `UV_PROJECT_ENVIRONMENT` relocates the project venv out of the plugin install dir (verified: with
  `UV_PROJECT_ENVIRONMENT=<path> uv run --directory <dir> --locked ...`, uv printed `Creating virtual environment at:
  <path>`, installed the 36 locked packages there, and `sys.prefix` inside the server was `<path>`). `.mcp.json` also supports `${VAR}` / `${VAR:-default}` expansion. Claude Code's server start-up timeout
  is `MCP_TIMEOUT` (ms). Prefer `uv run --directory` over `uvx --from` because of the stale-wheel behaviour above.
- **Noise control:** set `logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)` or pass
  `FastMCP(..., log_level="WARNING")`.

---

## 7. `title`, `meta`, `instructions`

- `@mcp.tool(title=..., meta=...)` -- both exist in 1.28.1 (and 1.30.0, 2.2.0) with the signature in section 1.
  Verified on the wire: `"title": "Get song info"` and `"meta": {"category": "song"}` (serialised as `_meta`) in
  `tools/list`. `ToolAnnotations` also has its own `title` field; `types.Tool.title` is the one FastMCP sets from the
  decorator.
- `FastMCP(instructions=...)` -- second positional parameter of the constructor (`instructions: str | None = None`),
  forwarded to the low-level `Server(instructions=...)` and returned in `InitializeResult.instructions`. Verified:
  the client printed `instructions: Experimental server. Use get_song_info to read state.` after `initialize()`.
  Available in tools as `ctx.fastmcp.instructions`.
- Also available on the constructor: `website_url`, `icons` (`mcp.server.fastmcp.Icon`); on `@mcp.resource(...)`:
  `title`, `meta`, `annotations`; on `@mcp.prompt(...)`: `title`, `icons`.

---

## Recommended skeleton (verified end to end with uv 0.8.17, mcp 1.30.0)

Layout:

```
server/
├── pyproject.toml
├── uv.lock                     # commit it; `uv run --locked` then guarantees reproducible installs
├── .python-version             # optional, e.g. "3.11"
├── src/ableton_live_mcp/__init__.py
└── tests/test_server.py
```

### `pyproject.toml`

```toml
[project]
name = "ableton-live-mcp"
version = "0.1.0"
description = "Ableton Live MCP server (stdio) for the Claude Code plugin"
requires-python = ">=3.11"
dependencies = ["mcp>=1.28,<2"]

[project.scripts]
ableton-live-mcp = "ableton_live_mcp:main"

[build-system]
requires = ["uv_build>=0.8.17,<0.9.0"]
build-backend = "uv_build"

# --- hatchling alternative (also verified) ---
# [build-system]
# requires = ["hatchling"]
# build-backend = "hatchling.build"
# [tool.hatch.build.targets.wheel]
# packages = ["src/ableton_live_mcp"]

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### `src/ableton_live_mcp/__init__.py`

```python
"""Ableton Live MCP server -- stdio transport, mcp 1.x FastMCP API."""
from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

# stdout is the JSON-RPC wire: log to stderr only, never print().
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
log = logging.getLogger("ableton_live_mcp")


@dataclass
class AppState:
    connected: bool = False


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppState]:
    log.info("startup")
    state = AppState(connected=True)  # open sockets / connections here
    try:
        yield state
    finally:
        log.info("shutdown")


mcp = FastMCP(
    "ableton-live-mcp",
    instructions="Tools for inspecting and controlling an Ableton Live session.",
    lifespan=lifespan,
)


@mcp.tool(
    title="Get song info",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
)
async def get_song_info(ctx: Context) -> dict[str, Any]:
    """Return tempo, track count and connection state."""
    state: AppState = ctx.request_context.lifespan_context
    if not state.connected:
        raise ToolError("Not connected to Ableton Live")
    await ctx.info("get_song_info called")
    return {"tempo": 120.0, "tracks": 3, "connected": state.connected}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### `tests/test_server.py`

```python
from mcp.shared.memory import create_connected_server_and_client_session as client_session

from ableton_live_mcp import mcp


async def test_get_song_info_structured():
    async with client_session(mcp._mcp_server) as client:
        res = await client.call_tool("get_song_info", {})
    assert res.isError is False
    assert res.structuredContent == {"tempo": 120.0, "tracks": 3, "connected": True}
```

Run: `uv sync` (once) then `uv run pytest`; launch manually with `uv run --directory server --locked ableton-live-mcp`
and, if `mcp[cli]` is installed, `uv run --with "mcp[cli]" mcp dev src/ableton_live_mcp/__init__.py` for the Inspector.

---

## Verification status summary

| Claim | Status |
| :- | :- |
| 1.28.1 / 1.30.0 signatures, source behaviour, wire output, timings, uv_build/hatchling builds, pytest run | Verified locally |
| PyPI versions/dates; 2.2.0 import failure and signatures; v2 docs quotes | Verified (PyPI JSON, `uv run --with mcp==2.2.0`, py.sdk docs) |
| Spec text on stdout | Verified (raw spec repo, 2025-06-18) |
| uv auto-downloads Python | Verified from uv 0.8.17 docs source + `uv python list` output |
| `uvx --reinstall/--refresh` picks up source edits | UNVERIFIED (transient PyPI connect failures in sandbox) |
| Behaviour of Claude Code's MCP client on a stray stdout line | UNVERIFIED |
| Cold-start time with an empty uv cache / managed Python download | UNVERIFIED |
| Stock macOS python3 version | UNVERIFIED |
| `.mcp.json` entry above working inside Claude Code | UNVERIFIED as a whole (pieces verified) |
| `UV_PROJECT_ENVIRONMENT` relocating the venv for `uv run --directory --locked` | Verified locally (venv created at the given path, `sys.prefix` matched) |
