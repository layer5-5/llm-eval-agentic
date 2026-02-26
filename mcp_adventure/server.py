#!/usr/bin/env python3
"""MCP server for the space station text adventure."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from game_logic.engine import GameEngine

mcp = FastMCP("Space Station Epsilon")
engine = GameEngine()


@mcp.tool()
def look() -> str:
    """Look around the current room. Describes your surroundings, visible items, and exits."""
    return engine.execute("look")


@mcp.tool()
def go(direction: str) -> str:
    """Move to an adjacent room. Direction must be: north, south, east, or west."""
    return engine.execute(f"go {direction}")


@mcp.tool()
def take(item: str) -> str:
    """Pick up an item in the current room. Use the item's name as shown in room descriptions."""
    return engine.execute(f"take {item}")


@mcp.tool()
def use(item: str) -> str:
    """Use an item from your inventory in the current room."""
    return engine.execute(f"use {item}")


@mcp.tool()
def read(item: str) -> str:
    """Read an item from your inventory (e.g., a note or log)."""
    return engine.execute(f"read {item}")


@mcp.tool()
def inventory() -> str:
    """Check what items you are currently carrying."""
    return engine.execute("inventory")


@mcp.tool()
def help() -> str:
    """Show available commands and how to play."""
    return engine.execute("help")


@mcp.tool()
def status() -> str:
    """Get current game state: room, inventory, move count, and win status."""
    state = engine.get_state()
    lines = [
        f"Room: {state['current_room']}",
        f"Inventory: {', '.join(state['inventory']) or 'empty'}",
        f"Moves: {state['moves']}",
        f"Won: {state['won']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
