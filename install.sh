#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"
SERVICE_NAME=$(basename $SCRIPT_DIR)
echo "SERVICE_NAME: $SERVICE_NAME"
# set permissions for script files
chmod a+x $SCRIPT_DIR/restart.sh
chmod 744 $SCRIPT_DIR/restart.sh

chmod a+x $SCRIPT_DIR/uninstall.sh
chmod 744 $SCRIPT_DIR/uninstall.sh

chmod a+x $SCRIPT_DIR/service/run
chmod 755 $SCRIPT_DIR/service/run

chmod a+x $SCRIPT_DIR/service/log/run

# create sym-link to run script in deamon
ln -sfn $SCRIPT_DIR/service /service/$SERVICE_NAME

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]
then
    touch $filename
    chmod 755 $filename
    echo "#!/bin/bash" >> $filename
    echo >> $filename
fi

grep -qxF "$SCRIPT_DIR/install.sh" $filename || echo "$SCRIPT_DIR/install.sh" >> $filename

# Install GUI-v1 (Classic UI) files if they exist
guiv1SettingsFile="/opt/victronenergy/gui/qml/PageSettingsFronius.qml"

if [ -f "$guiv1SettingsFile" ]; then
    echo "INFO: Found GUI-v1, installing Classic UI support"
    if (( $(grep -c "PageSettingsHuaweiSUN2000" $guiv1SettingsFile) > 0)); then
        echo "INFO: $guiv1SettingsFile seems already modified for HuaweiSUN2000 -- skipping modification"
    else
        echo "INFO: Adding menu entry to $guiv1SettingsFile"
        sed -i "/model: VisibleItemModel/ r $SCRIPT_DIR/gui/menu_item.txt" $guiv1SettingsFile
    fi
    cp -av $SCRIPT_DIR/gui/*.qml /opt/victronenergy/gui/qml/
else
    echo "INFO: GUI-v1 not found at $guiv1SettingsFile, skipping Classic UI installation"
fi

# Install GUI-v2 (New UI) files if they exist
guiv2SettingsFile="/opt/victronenergy/gui-v2/pages/settings/PageSettings.qml"

if [ -f "$guiv2SettingsFile" ]; then
    echo "INFO: Found GUI-v2, installing New UI support"
    if (( $(grep -c "PageSettingsHuaweiSUN2000" $guiv2SettingsFile) > 0)); then
        echo "INFO: $guiv2SettingsFile seems already modified for HuaweiSUN2000 -- skipping modification"
    else
        echo "INFO: Adding menu entry to $guiv2SettingsFile"
        # Insert before the closing brace of the pv inverters section
        sed -i "/ListNavigationItem.*PV inverters/a\\$(cat $SCRIPT_DIR/gui-v2/menu_item.txt)" $guiv2SettingsFile
    fi
    cp -av $SCRIPT_DIR/gui-v2/*.qml /opt/victronenergy/gui-v2/pages/settings/
else
    echo "INFO: GUI-v2 not found at $guiv2SettingsFile, skipping New UI installation"
fi

# As we've modified the GUI, we need to restart it
if [ -f "$guiv1SettingsFile" ] || [ -f "$guiv2SettingsFile" ]; then
    svc -t /service/gui
fi

