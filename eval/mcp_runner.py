"""MCP runner: wraps GameEngine as tool-callable functions for litellm tool calling."""

import json
from game_logic.engine import GameEngine

# OpenAI function-calling tool schemas
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "look",
            "description": "Examine your current surroundings. Shows the room description, exits, and any visible items.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "go",
            "description": "Move in a direction to another room.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "The direction to move (north, south, east, west)",
                        "enum": ["north", "south", "east", "west"],
                    }
                },
                "required": ["direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take",
            "description": "Pick up an item in the current room.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The name of the item to pick up (e.g. 'flashlight', 'keycard', 'crew log')",
                    }
                },
                "required": ["item"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "use",
            "description": "Use an item from your inventory in the current room.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The name of the item to use (e.g. 'flashlight', 'keycard')",
                    }
                },
                "required": ["item"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read an item you are carrying (e.g. a log or note).",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The name of the item to read (e.g. 'crew log')",
                    }
                },
                "required": ["item"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inventory",
            "description": "Check what items you are currently carrying.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


class McpRunner:
    def __init__(self):
        self.engine = GameEngine()

    def start(self) -> str:
        """Return the starting room description."""
        return self.engine.execute("look")

    def execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool call against the GameEngine. Returns narrative text."""
        if tool_name == "look":
            return self.engine.execute("look")
        elif tool_name == "go":
            direction = arguments.get("direction", "")
            return self.engine.execute(f"go {direction}")
        elif tool_name == "take":
            item = arguments.get("item", "")
            return self.engine.execute(f"take {item}")
        elif tool_name == "use":
            item = arguments.get("item", "")
            return self.engine.execute(f"use {item}")
        elif tool_name == "read":
            item = arguments.get("item", "")
            return self.engine.execute(f"read {item}")
        elif tool_name == "inventory":
            return self.engine.execute("inventory")
        else:
            return f"Unknown tool: '{tool_name}'"

    def check_win(self) -> bool:
        return self.engine.is_won()

    def reset(self):
        self.engine = GameEngine()
