#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"

# Kill processes if they exist (suppress errors if they don't)
pkill -f "dbus-huaweisun2000-pvinverter.py" 2>/dev/null || true
sleep 1
