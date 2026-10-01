"""Tool registration: ``register_all(mcp, ctx)`` wires every tool module onto the server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import arrangement, automation, browser, clips, devices, notes, scenes, session, status, tracks, view
from .common import AppContext

MODULES = (status, session, tracks, scenes, clips, notes, devices, browser, arrangement, automation, view)


def register_all(mcp: FastMCP, ctx: AppContext) -> None:
    for module in MODULES:
        module.register(mcp, ctx)


__all__ = ["AppContext", "register_all"]
