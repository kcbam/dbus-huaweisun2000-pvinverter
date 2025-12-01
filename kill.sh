#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SERVICE_NAME=$(basename $SCRIPT_DIR)

echo "==================================================================="
echo "Stopping Huawei SUN2000 PV Inverter and Grid Meter Services"
echo "==================================================================="

# Remove service symlinks (prevents automatic restart)
if [ -L "/service/$SERVICE_NAME" ]; then
    echo "Removing PV inverter service symlink..."
    rm /service/$SERVICE_NAME
fi

if [ -L "/service/dbus-huaweisun2000-grid" ]; then
    echo "Removing grid meter service symlink..."
    rm /service/dbus-huaweisun2000-grid
fi

# Kill supervise processes
echo "Killing supervise processes..."
KILLED_SUPERVISE=0
pkill -f "supervise $SERVICE_NAME" 2>/dev/null && KILLED_SUPERVISE=1
pkill -f "supervise dbus-huaweisun2000-grid" 2>/dev/null && KILLED_SUPERVISE=1
if [ $KILLED_SUPERVISE -eq 1 ]; then
    echo "✓ Supervise processes terminated"
else
    echo "  No supervise processes found"
fi

# Kill Python service processes
echo "Killing Python service processes..."
KILLED_PYTHON=0
pkill -f "dbus-huaweisun2000-pvinverter.py" 2>/dev/null && KILLED_PYTHON=1
pkill -f "dbus-grid-meter.py" 2>/dev/null && KILLED_PYTHON=1
if [ $KILLED_PYTHON -eq 1 ]; then
    echo "✓ Python services terminated"
else
    echo "  No Python service processes found"
fi

# Wait a moment for processes to fully terminate
sleep 1

# Check if processes are still running
REMAINING=$(pgrep -f "dbus-huaweisun2000" | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo ""
    echo "WARNING: Some processes are still running. Attempting force kill..."
    pkill -9 -f "dbus-huaweisun2000" 2>/dev/null
    sleep 1

    STILL_REMAINING=$(pgrep -f "dbus-huaweisun2000" | wc -l)
    if [ $STILL_REMAINING -gt 0 ]; then
        echo "ERROR: Could not kill all processes. Manual intervention required."
        echo "Running processes:"
        ps aux | grep dbus-huaweisun2000 | grep -v grep
    else
        echo "✓ All processes forcefully terminated"
    fi
else
    echo "✓ All processes stopped successfully"
fi

# Make the service run script non-executable (additional safety)
chmod a-x $SCRIPT_DIR/service/run

echo ""
echo "==================================================================="
echo "Service stopped!"
echo "==================================================================="
echo "The service will not restart automatically."
echo ""
echo "To start the service again, run:"
echo "  $SCRIPT_DIR/install.sh"
echo "  or"
echo "  $SCRIPT_DIR/restart.sh"
echo "==================================================================="
