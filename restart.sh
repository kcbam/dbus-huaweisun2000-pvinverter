#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"
rm $SCRIPT_DIR/current.log

kill $(pgrep -f "python -u $SCRIPT_DIR/dbus-huaweisun2000-pvinverter.py")
