#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"
SERVICE_NAME=$(basename $SCRIPT_DIR)
echo "SERVICE_NAME: $SERVICE_NAME"
# set permissions for script files
chmod 755 $SCRIPT_DIR/restart.sh $SCRIPT_DIR/uninstall.sh $SCRIPT_DIR/service/run $SCRIPT_DIR/service/log/run

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

QT_QUICK_VERSION="`grep "import QtQuick" /opt/victronenergy/gui/qml/main.qml | cut -d ' ' -f 3`"
if [ -z "${QT_QUICK_VERSION}" ]; then
    echo "WARNING: Couldn't determine QtQuick version, assuming version 2"
    QT_QUICK_VERSION=2
fi
for QML_FILE in $SCRIPT_DIR/gui/*.qml; do
    echo "Placing ${QML_FILE} into /opt/victronenergy/gui/qml/`basename ${QML_FILE}`"
    cat ${QML_FILE} | sed -e s/%%QT_QUICK_VERSION%%/${QT_QUICK_VERSION}/g > /opt/victronenergy/gui/qml/`basename ${QML_FILE}`
done

# As we've modified the GUI, we need to restart it
svc -t /service/gui
