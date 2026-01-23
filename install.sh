#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"
SERVICE_NAME=$(basename $SCRIPT_DIR)
echo "SERVICE_NAME: $SERVICE_NAME"
# set permissions for script files
chmod 755 $SCRIPT_DIR/restart.sh $SCRIPT_DIR/uninstall.sh $SCRIPT_DIR/service/run

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

# The "PV inverters" page in Settings is somewhat specific for Fronius. Let's change that.
invertersSettingsFile="/opt/victronenergy/gui/qml/PageSettingsFronius.qml"

if (( $(grep -c "PageSettingsHuaweiSUN2000" $invertersSettingsFile) > 0)); then
    echo "INFO: $invertersSettingsFile seems already modified for HuaweiSUN2000 -- skipping modification"
else
    echo "INFO: Adding menu entry to $invertersSettingsFile"
    sed -i "/model: VisibleItemModel/ r $SCRIPT_DIR/gui/menu_item.txt" $invertersSettingsFile
fi

cp -av $SCRIPT_DIR/gui/*.qml /opt/victronenergy/gui/qml/

# As we've modified the GUI, we need to restart it
svc -t /service/gui

