#!/bin/bash
# Reset the bash adventure to its initial state
DIR="$(cd "$(dirname "$0")" && pwd)"
STATION="$DIR/station"

# Clear inventory
rm -f "$STATION/inventory/flashlight" "$STATION/inventory/keycard"

# Remove win marker
rm -f "$STATION/.win"

# Remove dynamically created scripts
rm -f "$STATION/engine_room/take_keycard"

# Reset engine room README
cat > "$STATION/engine_room/README" << 'EOF'
ENGINE ROOM - Space Station Epsilon

The engine room is pitch black. You can barely see anything.
You hear the hum of dormant machinery.

Near the entrance, you feel something on a shelf — it might be a flashlight.
Try: ./flashlight

Exits:
  west/ -> Corridor
EOF

echo "Adventure reset to initial state."
