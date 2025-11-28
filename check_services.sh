#!/bin/bash

echo "==================================================================="
echo "Huawei SUN2000 Services Diagnostic Check"
echo "==================================================================="
echo ""

# Check PV inverter service
echo "1. PV Inverter Service Status:"
echo "-------------------------------------------------------------------"
if [ -L "/service/dbus-huaweisun2000-pvinverter" ]; then
    echo "✓ Service symlink exists: /service/dbus-huaweisun2000-pvinverter"
    svstat /service/dbus-huaweisun2000-pvinverter
else
    echo "✗ Service symlink NOT found"
fi

if pgrep -f "dbus-huaweisun2000-pvinverter.py" > /dev/null; then
    echo "✓ PV inverter process is running"
    ps aux | grep "dbus-huaweisun2000-pvinverter.py" | grep -v grep
else
    echo "✗ PV inverter process NOT running"
fi
echo ""

# Check grid meter service
echo "2. Grid Meter Service Status:"
echo "-------------------------------------------------------------------"
if [ -L "/service/dbus-huaweisun2000-grid" ]; then
    echo "✓ Service symlink exists: /service/dbus-huaweisun2000-grid"
    svstat /service/dbus-huaweisun2000-grid
else
    echo "✗ Service symlink NOT found"
fi

if pgrep -f "dbus-grid-meter.py" > /dev/null; then
    echo "✓ Grid meter process is running"
    ps aux | grep "dbus-grid-meter.py" | grep -v grep
else
    echo "✗ Grid meter process NOT running (OK if no meter connected)"
fi
echo ""

# Check DBus services
echo "3. DBus Services:"
echo "-------------------------------------------------------------------"
if dbus -y | grep -q "com.victronenergy.pvinverter.sun2000"; then
    echo "✓ PV inverter DBus service registered"
else
    echo "✗ PV inverter DBus service NOT registered"
fi

if dbus -y | grep -q "com.victronenergy.grid.huawei_meter"; then
    echo "✓ Grid meter DBus service registered"
else
    echo "✗ Grid meter DBus service NOT registered (OK if no meter)"
fi
echo ""

# Helper function to read DBus value
read_dbus_value() {
    dbus-send --print-reply --system --dest="$1" "$2" \
        com.victronenergy.BusItem.GetValue 2>/dev/null | \
        awk '/variant/ {gsub(/variant +/,""); print}' | \
        awk '{print $NF}'
}

# Check meter data in PV service
echo "4. Meter Data in PV Service:"
echo "-------------------------------------------------------------------"
METER_STATUS=$(read_dbus_value com.victronenergy.pvinverter.sun2000 /Meter/Status)
if [ -n "$METER_STATUS" ] && [ "$METER_STATUS" != "0" ]; then
    echo "✓ Meter detected! Status: $METER_STATUS"
    echo "  Meter Power: $(read_dbus_value com.victronenergy.pvinverter.sun2000 /Meter/Power || echo 'N/A') W"
    echo "  Meter Import: $(read_dbus_value com.victronenergy.pvinverter.sun2000 /Meter/Energy/Import || echo 'N/A') kWh"
    echo "  Meter Export: $(read_dbus_value com.victronenergy.pvinverter.sun2000 /Meter/Energy/Export || echo 'N/A') kWh"
else
    echo "✗ No meter detected (Status: ${METER_STATUS:-0})"
    echo "  Connect a DTSU666-H or similar meter via RS485 to enable grid tracking"
fi
echo ""

# Check grid service data (if available)
echo "5. Grid Service Data:"
echo "-------------------------------------------------------------------"
GRID_CONNECTED=$(read_dbus_value com.victronenergy.grid.huawei_meter /Connected)
if [ -n "$GRID_CONNECTED" ] && [ "$GRID_CONNECTED" != "0" ]; then
    echo "✓ Grid service connected and reporting"
    echo "  Grid Power: $(read_dbus_value com.victronenergy.grid.huawei_meter /Ac/Power || echo 'N/A') W"
    echo "  Grid Import: $(read_dbus_value com.victronenergy.grid.huawei_meter /Ac/Energy/Forward || echo 'N/A') kWh"
    echo "  Grid Export: $(read_dbus_value com.victronenergy.grid.huawei_meter /Ac/Energy/Reverse || echo 'N/A') kWh"
else
    echo "✗ Grid service not connected (Status: ${GRID_CONNECTED:-N/A})"
fi
echo ""

# Check logs
echo "6. Recent Logs:"
echo "-------------------------------------------------------------------"
echo "PV Inverter (last 10 lines):"
if [ -f "/var/log/dbus-huaweisun2000-pvinverter/current" ]; then
    tail -10 /var/log/dbus-huaweisun2000-pvinverter/current | tai64nlocal
else
    echo "  Log file not found"
fi
echo ""
echo "Grid Meter (last 10 lines):"
if [ -f "/var/log/dbus-huaweisun2000-grid/current" ]; then
    tail -10 /var/log/dbus-huaweisun2000-grid/current | tai64nlocal
else
    echo "  Log file not found (OK if service not running)"
fi
echo ""

echo "==================================================================="
echo "Diagnostic check complete!"
echo "==================================================================="
