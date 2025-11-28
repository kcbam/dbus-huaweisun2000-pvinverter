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

# Install grid meter service (if meter is connected)
chmod a+x $SCRIPT_DIR/service-grid/run
chmod 755 $SCRIPT_DIR/service-grid/run
chmod a+x $SCRIPT_DIR/service-grid/log/run

# Check if meter is available before installing grid service
echo "Checking for connected grid meter..."
python3 -c "
from connector_modbus import ModbusDataCollector2000Delux
from settings import HuaweiSUN2000Settings
import sys
settings = HuaweiSUN2000Settings()
modbus = ModbusDataCollector2000Delux(
    host=settings.get('modbus_host'),
    port=settings.get('modbus_port'),
    modbus_unit=settings.get('modbus_unit'),
    power_correction_factor=settings.get('power_correction_factor')
)
meter_data = modbus.getMeterData()
sys.exit(0 if meter_data is not None else 1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "==================================================================="
    echo "Grid meter detected! Installing grid meter service..."
    echo "==================================================================="
    ln -sfn $SCRIPT_DIR/service-grid /service/dbus-huaweisun2000-grid
    echo "Grid meter service installed. VRM will now track grid import/export!"
else
    echo "INFO: No grid meter detected. Grid import/export tracking will not be available."
    echo "      To enable, connect a DTSU666-H or compatible meter to the inverter via RS485."
fi

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

# Optional: Install detail page for GUI-v1
# This provides a dedicated page showing comprehensive inverter data
if [ -f "$guiv1SettingsFile" ]; then
    echo ""
    echo "==================================================================="
    echo "Optional: Inverter Detail Page"
    echo "==================================================================="
    echo "A detailed inverter status page is available showing:"
    echo "  - Current status and power output"
    echo "  - Total energy production"
    echo "  - Per-phase data (L1, L2, L3)"
    echo "  - DC power and device information"
    echo ""
    echo "To install:"
    echo "  cp $SCRIPT_DIR/gui/PageHuaweiSUN2000Details.qml /opt/victronenergy/gui/qml/"
    echo ""
    echo "Then add a menu entry to /opt/victronenergy/gui/qml/PageMain.qml"
    echo "See README.md for detailed instructions."
    echo "==================================================================="
    echo ""
fi

# Optional: Install overview tile for GUI-v1
if [ -f "$guiv1SettingsFile" ]; then
    echo "==================================================================="
    echo "Optional: Overview Screen Tile"
    echo "==================================================================="
    echo "Add a dedicated tile to the overview screen showing:"
    echo "  - Current power output"
    echo "  - Total energy production"
    echo "  - Inverter status"
    echo ""
    echo "To install, see: $SCRIPT_DIR/gui/overview_tile_instructions.md"
    echo "Or check the README.md for quick instructions."
    echo "==================================================================="
    echo ""
fi

# As we've modified the GUI, we need to restart it
if [ -f "$guiv1SettingsFile" ] || [ -f "$guiv2SettingsFile" ]; then
    echo "Restarting GUI..."
    svc -t /service/gui
    echo "Installation complete!"
fi

