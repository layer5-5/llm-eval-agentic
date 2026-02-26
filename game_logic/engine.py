"""Core game engine — pure state machine, no I/O."""

from game_logic.world import ROOMS, ITEMS, START_ROOM, INITIAL_FLAGS


class GameEngine:
    def __init__(self):
        self.current_room = START_ROOM
        self.inventory: set[str] = set()
        self.flags = dict(INITIAL_FLAGS)
        self.taken_items: set[str] = set()
        self.moves = 0

    def execute(self, command: str) -> str:
        """Parse and execute a command. Returns narrative text."""
        command = command.strip().lower()
        if not command:
            return "Say something. Type 'help' for commands."

        parts = command.split(maxsplit=1)
        verb = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "look": self._look,
            "go": self._go,
            "take": self._take,
            "use": self._use,
            "inventory": self._inventory,
            "help": self._help,
            "read": self._read,
        }

        handler = dispatch.get(verb)
        if handler is None:
            return f"Unknown command: '{verb}'. Type 'help' for commands."

        self.moves += 1
        return handler(arg)

    def is_won(self) -> bool:
        return self.flags.get("console_activated", False)

    def get_state(self) -> dict:
        return {
            "current_room": self.current_room,
            "inventory": sorted(self.inventory),
            "flags": dict(self.flags),
            "moves": self.moves,
            "won": self.is_won(),
        }

    # -- command handlers --

    def _look(self, _arg: str) -> str:
        room = ROOMS[self.current_room]

        if self.current_room == "engine_room":
            if not self.flags["engine_room_lit"]:
                return room["description_dark"]
            elif "keycard" not in self.taken_items:
                return room["description_lit"]
            else:
                return room["description_looted"]

        if self.current_room == "med_bay":
            if "crew_log" in self.taken_items:
                return room["description_looted"]

        return room["description"]

    def _go(self, direction: str) -> str:
        if not direction:
            return "Go where? Specify a direction (north, south, east, west)."

        room = ROOMS[self.current_room]
        exits = room["exits"]

        if direction not in exits:
            available = ", ".join(exits.keys())
            return f"You can't go {direction}. Exits: {available}."

        self.current_room = exits[direction]
        return self._enter_room()

    def _enter_room(self) -> str:
        room = ROOMS[self.current_room]
        prefix = f"You enter the {room['name']}.\n\n"

        if self.current_room == "engine_room" and not self.flags["engine_room_lit"]:
            return prefix + room["description_dark"]

        if self.current_room == "engine_room":
            if "keycard" not in self.taken_items:
                return prefix + room["description_lit"]
            return prefix + room["description_looted"]

        if self.current_room == "med_bay" and "crew_log" in self.taken_items:
            return prefix + room["description_looted"]

        return prefix + room["description"]

    def _take(self, item_name: str) -> str:
        if not item_name:
            return "Take what?"

        item_name = item_name.replace("_", " ")

        for item_id, item in ITEMS.items():
            if item["name"] == item_name and item["location"] == self.current_room:
                if item_id in self.taken_items:
                    return f"You already took the {item_name}."

                condition = item.get("take_condition")
                if condition and not self.flags.get(condition, False):
                    return item.get("take_fail", "You can't take that right now.")

                self.inventory.add(item_id)
                self.taken_items.add(item_id)
                return f"You pick up the {item['name']}."

        return f"There's no '{item_name}' here to take."

    def _use(self, item_name: str) -> str:
        if not item_name:
            return "Use what?"

        item_name = item_name.replace("_", " ")

        # Map item names to item IDs for lookup
        item_id = None
        for iid, item in ITEMS.items():
            if item["name"] == item_name:
                item_id = iid
                break

        if item_id is None or item_id not in self.inventory:
            return f"You don't have a '{item_name}'."

        # Flashlight in engine room
        if item_id == "flashlight" and self.current_room == "engine_room":
            if self.flags["engine_room_lit"]:
                return "The flashlight is already on. The room is lit."
            self.flags["engine_room_lit"] = True
            return (
                "You switch on the flashlight. The beam cuts through the darkness. "
                "You can see the engine core now — and something glinting under "
                "a pile of debris near the wall. It looks like a keycard."
            )

        # Flashlight elsewhere
        if item_id == "flashlight":
            return "You wave the flashlight around. Nothing interesting here."

        # Keycard on bridge
        if item_id == "keycard" and self.current_room == "bridge":
            self.flags["console_activated"] = True
            return (
                "You slide the keycard into the console. Screens flicker to life. "
                "The station's distress beacon activates — a rescue signal pulses "
                "out into deep space.\n\n"
                "*** YOU WIN ***\n"
                f"Completed in {self.moves} moves."
            )

        # Keycard elsewhere
        if item_id == "keycard":
            return "There's nothing to use the keycard on here."

        # Crew log
        if item_id == "crew_log":
            return f"You read the crew log:\n\n{ITEMS['crew_log']['read_text']}"

        return f"You can't figure out how to use the {item_name} here."

    def _read(self, item_name: str) -> str:
        if not item_name:
            return "Read what?"
        item_name = item_name.replace("_", " ")
        if item_name == "crew log" and "crew_log" in self.inventory:
            return f"You read the crew log:\n\n{ITEMS['crew_log']['read_text']}"
        if item_name == "crew log":
            return "You don't have the crew log."
        return f"You can't read '{item_name}'."

    def _inventory(self, _arg: str) -> str:
        if not self.inventory:
            return "You aren't carrying anything."
        names = [ITEMS[i]["name"] for i in sorted(self.inventory)]
        return "You are carrying: " + ", ".join(names) + "."

    def _help(self, _arg: str) -> str:
        return (
            "Commands:\n"
            "  look          - Examine your surroundings\n"
            "  go <direction> - Move (north, south, east, west)\n"
            "  take <item>   - Pick up an item\n"
            "  use <item>    - Use an item\n"
            "  read <item>   - Read an item\n"
            "  inventory     - Check what you're carrying\n"
            "  help          - Show this message"
        )
