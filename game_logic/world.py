"""Space station world definition: rooms, items, connections, and puzzle logic."""

ROOMS = {
    "airlock": {
        "name": "Airlock",
        "description": (
            "You are in the station's airlock. Emergency lights pulse red. "
            "The outer hatch is sealed shut — vacuum on the other side. "
            "A door leads into the corridor to the north."
        ),
        "exits": {"north": "corridor"},
    },
    "corridor": {
        "name": "Corridor",
        "description": (
            "A long metal corridor stretches before you. Sparks drip from "
            "damaged ceiling panels. Doors lead to the bridge (north), "
            "engine room (east), and med bay (west). The airlock is to the south."
        ),
        "exits": {
            "south": "airlock",
            "north": "bridge",
            "east": "engine_room",
            "west": "med_bay",
        },
    },
    "bridge": {
        "name": "Bridge",
        "description": (
            "The bridge is silent. A large console dominates the center of the room. "
            "Its screen is dark — it looks like it needs a keycard to activate. "
            "The corridor is to the south."
        ),
        "exits": {"south": "corridor"},
    },
    "engine_room": {
        "name": "Engine Room",
        "description_dark": (
            "The engine room is pitch black. You can barely see anything. "
            "You hear the hum of dormant machinery. "
            "Near the entrance, you feel something on a shelf — it might be a flashlight. "
            "The corridor is back to the west."
        ),
        "description_lit": (
            "The flashlight reveals a massive engine core surrounded by catwalks. "
            "Under a pile of debris near the wall, you spot a glinting keycard. "
            "The corridor is back to the west."
        ),
        "description_looted": (
            "The engine room is lit by your flashlight. The debris pile "
            "has been disturbed where you found the keycard. "
            "The corridor is back to the west."
        ),
        "exits": {"west": "corridor"},
    },
    "med_bay": {
        "name": "Med Bay",
        "description": (
            "A small medical bay with overturned supply carts. "
            "A crew log sits on the counter — it might have useful information. "
            "The corridor is to the east."
        ),
        "description_looted": (
            "A small medical bay with overturned supply carts. "
            "The counter is bare — you already took the crew log. "
            "The corridor is to the east."
        ),
        "exits": {"east": "corridor"},
    },
}

ITEMS = {
    "flashlight": {
        "name": "flashlight",
        "description": "A heavy-duty flashlight. Still has battery.",
        "location": "engine_room",
    },
    "keycard": {
        "name": "keycard",
        "description": "A security keycard with the captain's photo on it.",
        "location": "engine_room",
        "take_condition": "engine_room_lit",
        "take_fail": "It's too dark to find anything in here.",
    },
    "crew_log": {
        "name": "crew log",
        "description": "A datapad with the last crew log entry.",
        "location": "med_bay",
        "read_text": (
            "CREW LOG - Day 247: Power failure hit deck 3. Captain stashed "
            "the emergency keycard in the engine room before the lights went out. "
            "Grab a flashlight if you head in there — it's pitch black."
        ),
    },
}

START_ROOM = "airlock"

# Flags that track puzzle state (all start False)
INITIAL_FLAGS = {
    "engine_room_lit": False,
    "console_activated": False,
}
