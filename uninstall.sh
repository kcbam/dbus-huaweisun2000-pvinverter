#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SERVICE_NAME=$(basename $SCRIPT_DIR)
filename=/data/rc.local

# Remove GUI-v1 modifications
guiv1SettingsFile="/opt/victronenergy/gui/qml/PageSettingsFronius.qml"
if [ -f "$guiv1SettingsFile" ]; then
    echo "INFO: Removing GUI-v1 modifications"
    sed -i '/dbus-huaweisun2000 start/,/dbus-huaweisun2000 end/d' $guiv1SettingsFile
    rm -f /opt/victronenergy/gui/qml/PageSettingsHuaweiSUN2000.qml

    # Remove optional detail page if installed
    if [ -f /opt/victronenergy/gui/qml/PageHuaweiSUN2000Details.qml ]; then
        echo "INFO: Removing optional detail page"
        rm -f /opt/victronenergy/gui/qml/PageHuaweiSUN2000Details.qml
    fi

    # Note about overview tile
    echo ""
    echo "==================================================================="
    echo "MANUAL CLEANUP REQUIRED: Overview Tile"
    echo "==================================================================="
    echo "If you installed the optional overview tile, you need to manually"
    echo "remove it from /opt/victronenergy/gui/qml/OverviewTiles.qml"
    echo ""
    echo "1. Restore from backup (if you created one):"
    echo "   cp /opt/victronenergy/gui/qml/OverviewTiles.qml.backup \\"
    echo "      /opt/victronenergy/gui/qml/OverviewTiles.qml"
    echo ""
    echo "2. Or manually edit the file and remove the OverviewSolarInverter"
    echo "   component that you added."
    echo ""
    echo "3. Also remove any menu entry from PageMain.qml if you added it."
    echo "==================================================================="
    echo ""
fi

# Remove GUI-v2 modifications
guiv2SettingsFile="/opt/victronenergy/gui-v2/pages/settings/PageSettings.qml"
if [ -f "$guiv2SettingsFile" ]; then
    echo "INFO: Removing GUI-v2 modifications"
    sed -i '/dbus-huaweisun2000 start/,/dbus-huaweisun2000 end/d' $guiv2SettingsFile
    rm -f /opt/victronenergy/gui-v2/pages/settings/PageSettingsHuaweiSUN2000.qml
fi

# Remove main pvinverter service
rm /service/$SERVICE_NAME
kill $(pgrep -f 'supervise dbus-huaweisun2000-pvinverter')
chmod a-x $SCRIPT_DIR/service/run
$SCRIPT_DIR/restart.sh

# Remove old grid meter service if it exists (from previous versions)
if [ -L "/service/dbus-grid-meter" ]; then
    echo "INFO: Removing old grid meter service"
    svc -d /service/dbus-grid-meter 2>/dev/null
    sleep 1
    rm -f /service/dbus-grid-meter
    kill $(pgrep -f 'supervise dbus-grid-meter') 2>/dev/null
fi

# Remove old grid meter files if they exist
rm -f $SCRIPT_DIR/dbus-grid-meter.py
rm -rf $SCRIPT_DIR/grid-service

# Remove from startup
STARTUP=$SCRIPT_DIR/install.sh
sed -i "\~$STARTUP~d" $filename

# Restart GUI if we made changes
if [ -f "$guiv1SettingsFile" ] || [ -f "$guiv2SettingsFile" ]; then
    svc -t /service/gui
fi
