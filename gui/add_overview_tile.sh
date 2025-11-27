#!/bin/bash

# Script to add Huawei inverter tile to Venus OS overview screen
# This adds an OverviewSolarInverter component to OverviewTiles.qml

TARGET_FILE="/opt/victronenergy/gui/qml/OverviewTiles.qml"
BACKUP_FILE="/opt/victronenergy/gui/qml/OverviewTiles.qml.backup"

# Check if target file exists
if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: $TARGET_FILE not found"
    echo "This script only works on Venus OS with GUI-v1 installed."
    exit 1
fi

# Check if already added
if grep -q "OverviewSolarInverter" "$TARGET_FILE"; then
    echo "INFO: OverviewSolarInverter tile already exists in $TARGET_FILE"
    echo "Nothing to do."
    exit 0
fi

# Create backup
echo "Creating backup: $BACKUP_FILE"
cp "$TARGET_FILE" "$BACKUP_FILE"

# Find the PV CHARGER tile and add OverviewSolarInverter after it
# Look for the closing brace of pvChargerTile
LINE_NUM=$(grep -n "id: pvChargerTile" "$TARGET_FILE" | cut -d: -f1)

if [ -z "$LINE_NUM" ]; then
    echo "ERROR: Could not find PV CHARGER tile in $TARGET_FILE"
    echo "The file structure may have changed."
    exit 1
fi

# Find the closing brace after pvChargerTile (scan forward from LINE_NUM)
CLOSING_BRACE_LINE=$(awk -v start="$LINE_NUM" '
    NR > start && /^[[:space:]]*\}[[:space:]]*$/ {
        print NR
        exit
    }
' "$TARGET_FILE")

if [ -z "$CLOSING_BRACE_LINE" ]; then
    echo "ERROR: Could not find closing brace for PV CHARGER tile"
    exit 1
fi

echo "Found PV CHARGER tile at line $LINE_NUM"
echo "Will insert OverviewSolarInverter after line $CLOSING_BRACE_LINE"

# Insert the tile after the closing brace
sed -i "${CLOSING_BRACE_LINE}a\\
\\
\t\t\t\tOverviewSolarInverter {\\
\t\t\t\t\twidth: 160\\
\t\t\t\t\theight: bottomRow.height\\
\t\t\t\t}" "$TARGET_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "==================================================================="
    echo "SUCCESS: Overview tile added!"
    echo "==================================================================="
    echo "The OverviewSolarInverter tile has been added to the overview screen."
    echo ""
    echo "Restarting GUI..."
    svc -t /service/gui
    echo ""
    echo "The tile should now appear on the overview screen."
    echo "It will show your Huawei inverter's current power and total energy."
    echo ""
    echo "To remove the tile, restore from backup:"
    echo "  cp $BACKUP_FILE $TARGET_FILE"
    echo "  svc -t /service/gui"
    echo "==================================================================="
else
    echo "ERROR: Failed to modify $TARGET_FILE"
    echo "Restoring from backup..."
    cp "$BACKUP_FILE" "$TARGET_FILE"
    exit 1
fi
