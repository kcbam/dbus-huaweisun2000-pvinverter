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
fi

# Remove GUI-v2 modifications
guiv2SettingsFile="/opt/victronenergy/gui-v2/pages/settings/PageSettings.qml"
if [ -f "$guiv2SettingsFile" ]; then
    echo "INFO: Removing GUI-v2 modifications"
    sed -i '/dbus-huaweisun2000 start/,/dbus-huaweisun2000 end/d' $guiv2SettingsFile
    rm -f /opt/victronenergy/gui-v2/pages/settings/PageSettingsHuaweiSUN2000.qml
fi

# Remove service
rm /service/$SERVICE_NAME
kill $(pgrep -f 'supervise dbus-huaweisun2000-pvinverter')
chmod a-x $SCRIPT_DIR/service/run
$SCRIPT_DIR/restart.sh

# Remove from startup
STARTUP=$SCRIPT_DIR/install.sh
sed -i "\~$STARTUP~d" $filename

# Restart GUI if we made changes
if [ -f "$guiv1SettingsFile" ] || [ -f "$guiv2SettingsFile" ]; then
    svc -t /service/gui
fi
