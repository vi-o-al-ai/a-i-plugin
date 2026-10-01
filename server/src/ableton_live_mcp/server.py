"""Build the FastMCP server: instructions, lifespan and all tool registrations."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from . import __version__
from .config import Settings
from .tools import AppContext, register_all

log = logging.getLogger("ableton_live_mcp.server")

SERVER_NAME = "ableton-live"

INSTRUCTIONS = (
    "Controls the Ableton Live 12 set open on this machine through the ClaudeLive Remote Script. "
    "Call ableton_status first to confirm Live is reachable, then get_session to learn the track, scene, "
    "clip and device indices; indices always come from your latest read and shift when tracks or scenes "
    "are created or deleted, so re-read after structural changes. "
    "Times are in beats (one 4/4 bar = 4.0), pitches are MIDI note numbers 0-127, velocities 1-127, "
    "volume is normalized 0-1 (0.85 is 0 dB) and device_path is a string like \"0\", \"0/1/2\" or \"mixer\". "
    "Destructive tools (delete_track, delete_scene, delete_clip, delete_device, clear_automation of all "
    "envelopes, remove_notes without a selector, add_clip_to_arrangement with delete_source) refuse to run "
    "unless confirm=True; ask the user before confirming, and before replace_notes on a clip the user wrote. "
    "Pass a short `why` on every mutating tool: it is never sent to Live but is written to the local action "
    "history so the session log reads as a narrative the user can review."
)


def build_server(settings: Settings, app: AppContext | None = None) -> FastMCP:
    """Create the server. ``app`` may be supplied (tests) to reach the client/history afterwards."""
    app = app if app is not None else AppContext(settings)

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
        app.start()
        log.info(
            "ableton-live-mcp %s starting; script at %s:%s; home %s",
            __version__,
            settings.host,
            settings.port,
            settings.home,
        )
        try:
            yield app
        finally:
            await app.aclose()
            log.info("ableton-live-mcp stopped")

    mcp = FastMCP(SERVER_NAME, instructions=INSTRUCTIONS, lifespan=lifespan, log_level=settings.log_level)  # type: ignore[arg-type]
    register_all(mcp, app)
    return mcp
