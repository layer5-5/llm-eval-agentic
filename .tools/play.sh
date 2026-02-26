#!/bin/bash
# Play the bash adventure yourself (manual mode)
set -e
cd "$(dirname "$0")/.."

bash bash_adventure/reset.sh
echo ""
cat bash_adventure/station/START
echo ""
cd bash_adventure/station/airlock
exec bash --norc --noprofile
