#!/bin/bash

echo "==================================================================="
echo "Venus OS System Calculator Diagnostic"
echo "==================================================================="
echo ""

# Helper function to read DBus value
read_dbus_value() {
    dbus-send --print-reply --system --dest="$1" "$2" \
        com.victronenergy.BusItem.GetValue 2>/dev/null | \
        sed -n 's/.*variant.*\(int32\|double\|string\) \([-0-9."]*\).*/\2/p'
}

# Check if system calculator service is running
echo "1. System Calculator Service:"
echo "-------------------------------------------------------------------"
if dbus -y | grep -q "com.victronenergy.system"; then
    echo "✓ System calculator service registered"
else
    echo "✗ System calculator service NOT registered"
    echo "  System calculator is required for consumption calculation"
fi
echo ""

# Check grid meter registration with system
echo "2. Grid Meter Registration:"
echo "-------------------------------------------------------------------"
echo "Grid meter DBus service:"
GRID_CONNECTED=$(read_dbus_value com.victronenergy.grid.huawei_meter /Connected)
echo "  /Connected: ${GRID_CONNECTED:-N/A}"
echo "  /DeviceType: $(read_dbus_value com.victronenergy.grid.huawei_meter /DeviceType || echo 'N/A')"
echo "  /ProductId: $(read_dbus_value com.victronenergy.grid.huawei_meter /ProductId || echo 'N/A')"
echo "  /DeviceInstance: $(read_dbus_value com.victronenergy.grid.huawei_meter /DeviceInstance || echo 'N/A')"
echo "  /Role: $(read_dbus_value com.victronenergy.grid.huawei_meter /Role || echo 'N/A')"
echo "  /Ac/Power: $(read_dbus_value com.victronenergy.grid.huawei_meter /Ac/Power || echo 'N/A') W"
echo "  /Ac/L1/Power: $(read_dbus_value com.victronenergy.grid.huawei_meter /Ac/L1/Power || echo 'N/A') W"
echo "  /Ac/NumberOfPhases: $(read_dbus_value com.victronenergy.grid.huawei_meter /Ac/NumberOfPhases || echo 'N/A')"
echo ""

# Check PV inverter registration
echo "3. PV Inverter Registration:"
echo "-------------------------------------------------------------------"
echo "PV inverter DBus service:"
echo "  /Ac/Power: $(read_dbus_value com.victronenergy.pvinverter.sun2000 /Ac/Power || echo 'N/A') W"
echo "  /DeviceInstance: $(read_dbus_value com.victronenergy.pvinverter.sun2000 /DeviceInstance || echo 'N/A')"
echo "  /Position: $(read_dbus_value com.victronenergy.pvinverter.sun2000 /Position || echo 'N/A')"
echo ""

# Check what system calculator sees
echo "4. System Calculator Values:"
echo "-------------------------------------------------------------------"
echo "Trying to read system calculator paths (may timeout if not working):"
echo -n "  /Ac/Grid/DeviceType: "
timeout 2 dbus-send --print-reply --system \
    --dest=com.victronenergy.system \
    /Ac/Grid/DeviceType com.victronenergy.BusItem.GetValue 2>&1 | \
    sed -n 's/.*variant.*\(int32\|double\) \([-0-9.]*\).*/\2/p' || echo "TIMEOUT or ERROR"

echo -n "  /Ac/Grid/L1/Power: "
timeout 2 dbus-send --print-reply --system \
    --dest=com.victronenergy.system \
    /Ac/Grid/L1/Power com.victronenergy.BusItem.GetValue 2>&1 | \
    sed -n 's/.*variant.*\(int32\|double\) \([-0-9.]*\).*/\2/p' || echo "TIMEOUT or ERROR"

echo -n "  /Ac/Consumption/L1/Power: "
timeout 2 dbus-send --print-reply --system \
    --dest=com.victronenergy.system \
    /Ac/Consumption/L1/Power com.victronenergy.BusItem.GetValue 2>&1 | \
    sed -n 's/.*variant.*\(int32\|double\) \([-0-9.]*\).*/\2/p' || echo "TIMEOUT or ERROR"

echo -n "  /Ac/PvOnGrid/L1/Power: "
timeout 2 dbus-send --print-reply --system \
    --dest=com.victronenergy.system \
    /Ac/PvOnGrid/L1/Power com.victronenergy.BusItem.GetValue 2>&1 | \
    sed -n 's/.*variant.*\(int32\|double\) \([-0-9.]*\).*/\2/p' || echo "TIMEOUT or ERROR"
echo ""

# Check system calculator settings
echo "5. System Calculator Settings:"
echo "-------------------------------------------------------------------"
if [ -f "/data/conf/settings.xml" ]; then
    echo "Checking settings.xml for relevant entries:"
    grep -A 2 "HasAcInputMeasurement\|HasGridMeter\|HasAcOutMeasurement" /data/conf/settings.xml | head -20
else
    echo "  Settings file not found"
fi
echo ""

# Check dbus-systemcalc process
echo "6. System Calculator Process:"
echo "-------------------------------------------------------------------"
if pgrep -f "systemcalc" > /dev/null; then
    echo "✓ System calculator process is running"
    PID=$(pgrep -f "systemcalc")
    echo "  PID: $PID"
    echo "  Process: $(ps | grep $PID | grep -v grep)"
else
    echo "✗ System calculator process NOT running"
fi
echo ""

# Check recent system calculator logs
echo "7. System Calculator Logs:"
echo "-------------------------------------------------------------------"
if [ -f "/var/log/dbus-systemcalc-py/current" ]; then
    echo "Last 20 lines from system calculator log:"
    tail -20 /var/log/dbus-systemcalc-py/current | tai64nlocal
else
    echo "  Log file not found"
fi
echo ""

echo "==================================================================="
echo "Diagnostic complete!"
echo "==================================================================="
echo ""
echo "Expected behavior:"
echo "  - Grid meter should have /Connected = 1"
echo "  - Grid meter should have /DeviceType = 345"
echo "  - System calculator should respond (not timeout)"
echo "  - Consumption = Grid Power + PV Power"
echo ""
