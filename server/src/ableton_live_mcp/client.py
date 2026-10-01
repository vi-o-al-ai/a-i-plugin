"""Async JSON-RPC 2.0 client for the ClaudeLive Remote Script (PROTOCOL.md sections 1, 2, 8).

One persistent TCP connection, opened lazily, with request/response pairs serialised by a
lock. Any connection failure closes the socket so the next call reconnects transparently.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from .errors import INTERNAL_ERROR, LiveError

log = logging.getLogger("ableton_live_mcp.client")

MAX_LINE = 4 * 1024 * 1024  # PROTOCOL.md section 1: 4 MiB per line

READ_TIMEOUT = 5.0
MUTATION_TIMEOUT = 15.0
LONG_TIMEOUT = 60.0
CONNECT_TIMEOUT = 5.0

# Timeouts by method prefix (trailing dot) or exact method name. Exact names win over
# prefixes; anything not listed is classified as a read (5 s) or a mutation (15 s).
TIMEOUTS: dict[str, float] = {
    "browser.": LONG_TIMEOUT,
    "song.get_overview": LONG_TIMEOUT,
    "sys.describe_api": LONG_TIMEOUT,
    "sys.ping": READ_TIMEOUT,
}

_READ_SUFFIXES = ("get", "list", "ping", "search")


def is_read_method(method: str) -> bool:
    tail = method.rsplit(".", 1)[-1]
    return tail.startswith(_READ_SUFFIXES)


def timeout_for(method: str, overrides: dict[str, float] | None = None) -> float:
    """Pick the PROTOCOL.md section 8 timeout for ``method``."""
    for table in (overrides or {}, TIMEOUTS):
        if method in table:
            return table[method]
    best: tuple[int, float] | None = None
    for table in (overrides or {}, TIMEOUTS):
        for key, value in table.items():
            if key.endswith(".") and method.startswith(key) and (best is None or len(key) > best[0]):
                best = (len(key), value)
    if best is not None:
        return best[1]
    return READ_TIMEOUT if is_read_method(method) else MUTATION_TIMEOUT


class LiveClient:
    """Thin client; ``await client.call(method, params)`` returns the result dict or raises ``LiveError``."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9892, *, connect_timeout: float = CONNECT_TIMEOUT):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.timeout_overrides: dict[str, float] = {}
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._next_id = 1
        self.connect_count = 0

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    # -- connection management --------------------------------------------------------

    async def _connect(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port, limit=MAX_LINE),
                timeout=self.connect_timeout,
            )
        except asyncio.TimeoutError:
            raise LiveError("TIMEOUT", f"Connecting to Live at {self.address} timed out") from None
        except ConnectionRefusedError:
            raise LiveError(
                "CONNECTION",
                f"Could not connect to Live at {self.address} (connection refused)",
                {"host": self.host, "port": self.port},
            ) from None
        except OSError as exc:
            raise LiveError(
                "CONNECTION",
                f"Could not connect to Live at {self.address} ({exc.strerror or exc})",
                {"host": self.host, "port": self.port},
            ) from None
        self.connect_count += 1
        log.info("connected to ClaudeLive at %s", self.address)

    async def close(self) -> None:
        """Drop the connection (idempotent). The next ``call`` reconnects."""
        writer, self._writer, self._reader = self._writer, None, None
        if writer is None:
            return
        try:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
        except Exception:  # noqa: BLE001 - closing a dead socket may raise anything
            pass

    # -- requests ---------------------------------------------------------------------

    async def call(self, method: str, params: dict[str, Any] | None = None, timeout: float | None = None) -> dict[str, Any]:
        """Send one request and wait for its response."""
        if timeout is None:
            timeout = timeout_for(method, self.timeout_overrides)
        async with self._lock:
            if not self.connected:
                await self._connect()
            assert self._reader is not None and self._writer is not None
            req_id = self._next_id
            self._next_id += 1
            request = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
            line = json.dumps(request, separators=(",", ":"), ensure_ascii=False) + "\n"
            try:
                self._writer.write(line.encode("utf-8"))
                await self._writer.drain()
                raw = await asyncio.wait_for(self._reader.readline(), timeout=timeout)
            except asyncio.TimeoutError:
                await self.close()
                raise LiveError(
                    "TIMEOUT",
                    f"No response from Live within {timeout:g} s for {method}",
                    {"method": method, "timeout": timeout},
                ) from None
            except (ConnectionError, asyncio.IncompleteReadError) as exc:
                await self.close()
                raise LiveError("CONNECTION", f"Connection to Live at {self.address} was lost during {method} ({exc})") from None
            except ValueError as exc:  # readline(): line longer than MAX_LINE
                await self.close()
                raise LiveError("PROTOCOL", f"Response to {method} exceeded the 4 MiB line limit ({exc})") from None
            except OSError as exc:
                await self.close()
                raise LiveError("CONNECTION", f"Connection to Live at {self.address} failed during {method} ({exc})") from None

            if not raw:
                await self.close()
                raise LiveError("CONNECTION", f"Live closed the connection at {self.address} while handling {method}")

            return await self._parse_response(raw, req_id, method)

    async def _parse_response(self, raw: bytes, req_id: int, method: str) -> dict[str, Any]:
        snippet = raw[:300].decode("utf-8", "replace").rstrip("\n")
        try:
            message = json.loads(raw)
        except ValueError:
            await self.close()
            raise LiveError("PROTOCOL", f"Live sent invalid JSON in response to {method}: {snippet!r}") from None
        if not isinstance(message, dict):
            await self.close()
            raise LiveError("PROTOCOL", f"Live sent a non-object response to {method}: {snippet!r}")
        if message.get("id") != req_id:
            await self.close()
            raise LiveError(
                "PROTOCOL",
                f"Live answered request {req_id} ({method}) with id {message.get('id')!r}: {snippet!r}",
            )
        error = message.get("error")
        if error is not None:
            if not isinstance(error, dict):
                raise LiveError(INTERNAL_ERROR, f"Malformed error object from Live: {snippet!r}")
            raise LiveError(error.get("code", INTERNAL_ERROR), str(error.get("message", "Unknown error")), error.get("data"))
        result = message.get("result")
        if not isinstance(result, dict):
            raise LiveError("PROTOCOL", f"Live returned a non-object result for {method}: {snippet!r}")
        return result

    async def ping(self) -> dict[str, Any]:
        """``sys.ping`` plus the measured round trip in milliseconds."""
        started = time.perf_counter()
        result = dict(await self.call("sys.ping", {}))
        result["round_trip_ms"] = round((time.perf_counter() - started) * 1000.0, 1)
        return result
