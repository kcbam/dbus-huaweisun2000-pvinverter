#!/bin/bash

# Cleanup script for old grid meter service
# This service was removed in favor of integrated meter data on the pvinverter service
# Run this script if you see DBus errors for com.victronenergy.grid.huawei_meter

echo "==========================================================================="
echo "Cleaning up old grid meter service (com.victronenergy.grid.huawei_meter)"
echo "==========================================================================="
echo ""

# Check if the old service exists
if [ -L "/service/dbus-grid-meter" ]; then
    echo "Found old grid meter service symlink, removing..."

    # Stop the service
    echo "Stopping service..."
    svc -d /service/dbus-grid-meter 2>/dev/null

    # Wait a moment for it to stop
    sleep 2

    # Remove the symlink
    echo "Removing service symlink..."
    rm -f /service/dbus-grid-meter

    echo "✓ Old grid meter service removed"
else
    echo "No old grid meter service found (this is good!)"
fi

# Check for old service files in /data
if [ -f "/data/dbus-huaweisun2000-pvinverter/dbus-grid-meter.py" ]; then
    echo ""
    echo "Found old grid meter service file, removing..."
    rm -f /data/dbus-huaweisun2000-pvinverter/dbus-grid-meter.py
    echo "✓ Old service file removed"
fi

# Check for old service directory
if [ -d "/data/dbus-huaweisun2000-pvinverter/grid-service" ]; then
    echo ""
    echo "Found old grid service directory, removing..."
    rm -rf /data/dbus-huaweisun2000-pvinverter/grid-service
    echo "✓ Old service directory removed"
fi

echo ""
echo "==========================================================================="
echo "Cleanup complete!"
echo "==========================================================================="
echo ""
echo "The meter data is now integrated into the main pvinverter service:"
echo "  Service: com.victronenergy.pvinverter.sun2000"
echo "  Paths: /Meter/Power, /Meter/Energy/Import, /Meter/Energy/Export, etc."
echo ""
echo "You can verify with:"
echo "  dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Status GetValue"
echo ""
echo "If you still see errors in /var/log/gui/current, restart the GUI:"
echo "  svc -t /service/gui"
echo ""
