#!/bin/bash
echo "==================================================================="
echo "Service Status Check"
echo "==================================================================="
echo ""

echo "1. Checking for running processes:"
ps aux | grep -E "dbus-huaweisun2000|python.*pvinverter" | grep -v grep
echo ""

echo "2. Checking service symlink:"
ls -la /service/ | grep huawei
echo ""

echo "3. Checking if service run script is executable:"
ls -la /data/dbus-huaweisun2000-pvinverter/service/run
echo ""

echo "4. Checking recent logs (last 30 lines):"
if [ -f /var/log/dbus-huaweisun2000-pvinverter/current ]; then
    tail -30 /var/log/dbus-huaweisun2000-pvinverter/current
else
    echo "No log file found at /var/log/dbus-huaweisun2000-pvinverter/current"
fi
echo ""

echo "5. Checking DBus services:"
dbus -y 2>/dev/null | grep -E "pvinverter.sun2000|grid.huawei" || echo "DBus command not available or no services found"
echo ""

echo "==================================================================="
