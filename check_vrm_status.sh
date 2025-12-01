#!/bin/bash

echo "=============================================="
echo "Huawei SUN2000 VRM Status Diagnostic"
echo "=============================================="
echo ""

echo "1. Checking PV Inverter Service"
echo "--------------------------------"
if svstat /service/dbus-huaweisun2000-pvinverter 2>/dev/null; then
    echo "✓ PV inverter service is running"
else
    echo "✗ PV inverter service is NOT running"
fi
echo ""

echo "2. Checking Grid Meter Service"
echo "--------------------------------"
if svstat /service/dbus-huaweisun2000-grid 2>/dev/null; then
    echo "✓ Grid meter service is running"
else
    echo "✗ Grid meter service is NOT running or not installed"
fi
echo ""

echo "3. Checking DBus Services"
echo "--------------------------------"
echo "PV Inverter DBus Service:"
if dbus -y com.victronenergy.pvinverter.sun2000 / GetValue 2>/dev/null >/dev/null; then
    echo "  ✓ com.victronenergy.pvinverter.sun2000 is registered"

    # Check inverter data
    AC_POWER=$(dbus -y com.victronenergy.pvinverter.sun2000 /Ac/Power GetValue 2>/dev/null)
    AC_ENERGY=$(dbus -y com.victronenergy.pvinverter.sun2000 /Ac/Energy/Forward GetValue 2>/dev/null)
    echo "  - AC Power: ${AC_POWER}W"
    echo "  - Total Energy: ${AC_ENERGY}kWh"

    # Check meter data
    METER_STATUS=$(dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Status GetValue 2>/dev/null)
    METER_POWER=$(dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Power GetValue 2>/dev/null)
    echo "  - Meter Status: $METER_STATUS (1=detected, 0=not detected)"
    echo "  - Meter Power: ${METER_POWER}W"
else
    echo "  ✗ com.victronenergy.pvinverter.sun2000 is NOT registered"
fi
echo ""

echo "Grid Meter DBus Service:"
if dbus -y com.victronenergy.grid.huawei_meter / GetValue 2>/dev/null >/dev/null; then
    echo "  ✓ com.victronenergy.grid.huawei_meter is registered"

    GRID_POWER=$(dbus -y com.victronenergy.grid.huawei_meter /Ac/Power GetValue 2>/dev/null)
    GRID_CONNECTED=$(dbus -y com.victronenergy.grid.huawei_meter /Connected GetValue 2>/dev/null)
    echo "  - Grid Power: ${GRID_POWER}W (positive=import, negative=export)"
    echo "  - Connected: $GRID_CONNECTED (1=yes, 0=no)"
else
    echo "  ✗ com.victronenergy.grid.huawei_meter is NOT registered"
    echo "  → This is why grid data doesn't show in VRM portal!"
fi
echo ""

echo "4. Checking VRM Portal Connection"
echo "--------------------------------"
VRM_PORTAL_ID=$(cat /etc/venus/unique-id 2>/dev/null || echo "NOT FOUND")
echo "VRM Portal ID: $VRM_PORTAL_ID"

if [ -f /data/vrm_portal_id ]; then
    echo "VRM Portal connected: Yes"
else
    echo "VRM Portal connected: Check Settings -> VRM Portal"
fi
echo ""

echo "5. Recent PV Inverter Log (last 20 lines)"
echo "--------------------------------"
tail -n 20 /var/log/dbus-huaweisun2000/current 2>/dev/null | tai64nlocal 2>/dev/null || tail -n 20 /var/log/dbus-huaweisun2000/current 2>/dev/null
echo ""

echo "6. Recent Grid Meter Log (last 20 lines)"
echo "--------------------------------"
if [ -f /var/log/dbus-huaweisun2000-grid/current ]; then
    tail -n 20 /var/log/dbus-huaweisun2000-grid/current 2>/dev/null | tai64nlocal 2>/dev/null || tail -n 20 /var/log/dbus-huaweisun2000-grid/current 2>/dev/null
else
    echo "✗ No grid meter logs found (service not running or never started)"
fi
echo ""

echo "=============================================="
echo "Diagnosis Summary"
echo "=============================================="
echo ""
echo "To fix 'nothing showing on VRM':"
echo ""
echo "If PV inverter service is NOT running:"
echo "  1. Check Settings -> PV Inverters -> Huawei SUN2000"
echo "  2. Verify Modbus Host IP is correct (not 192.168.255.255)"
echo "  3. Restart service: sh /data/dbus-huaweisun2000-pvinverter/restart.sh"
echo ""
echo "If Grid meter service is NOT running:"
echo "  1. Re-run installer: sh /data/dbus-huaweisun2000-pvinverter/install.sh"
echo "  2. Check if meter is detected (Meter Status should be 1)"
echo "  3. The grid service requires meter to be connected via RS485"
echo ""
echo "If services ARE running but data not showing:"
echo "  1. Check VRM Portal connection: Settings -> VRM Portal"
echo "  2. Wait 15-30 minutes for data to appear on VRM Portal"
echo "  3. Check local GUI shows data (overview screen)"
echo ""
echo "For more help, provide output of this script on GitHub issue"
echo "=============================================="
