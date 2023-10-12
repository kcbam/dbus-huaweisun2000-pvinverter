#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"
rm $SCRIPT_DIR/current.log

kill $(pgrep -f "python $SCRIPT_DIR/dbus-sun2000-pvinverter.py")
