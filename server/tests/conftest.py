"""Fixtures: a fake Remote Script on an ephemeral port, settings pointing at it, an in-memory MCP client."""

from __future__ import annotations

import asyncio
import socket
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session

from ableton_live_mcp.config import Settings
from ableton_live_mcp.server import build_server
from ableton_live_mcp.tools.common import AppContext

from .fake_script import FakeScript


def free_port() -> int:
    """A port nothing listens on (bound and released)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
async def fake_script() -> AsyncIterator[FakeScript]:
    fake = await FakeScript().start()
    try:
        yield fake
    finally:
        await fake.stop()


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "claude-live-home"


@pytest.fixture
def settings(fake_script: FakeScript, home: Path) -> Settings:
    return Settings(host="127.0.0.1", port=fake_script.port, home=home)


@pytest.fixture
def app(settings: Settings) -> AppContext:
    return AppContext(settings)


@pytest.fixture
def server(settings: Settings, app: AppContext) -> FastMCP:
    return build_server(settings, app=app)


@pytest.fixture
async def client(server: FastMCP) -> AsyncIterator[ClientSession]:
    """An initialised in-memory client session.

    The session's task group must be entered and exited by the same task, and pytest-asyncio
    runs fixture setup and teardown in different tasks, so a helper task owns the session.
    """
    ready: asyncio.Event = asyncio.Event()
    stop: asyncio.Event = asyncio.Event()
    holder: dict[str, ClientSession] = {}

    async def runner() -> None:
        async with create_connected_server_and_client_session(server) as session:
            holder["session"] = session
            ready.set()
            await stop.wait()

    task = asyncio.create_task(runner())
    waiter = asyncio.ensure_future(ready.wait())
    done, _ = await asyncio.wait({task, waiter}, return_when=asyncio.FIRST_COMPLETED)
    if task in done:
        waiter.cancel()
        task.result()  # raises the startup error
        raise RuntimeError("MCP session ended before it was ready")
    try:
        yield holder["session"]
    finally:
        stop.set()
        await task


@pytest.fixture
def closed_port_settings(home: Path) -> Settings:
    return Settings(host="127.0.0.1", port=free_port(), home=home)
