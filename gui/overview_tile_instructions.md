# Adding Huawei Inverter Tile to Overview Screen

## Overview

This guide explains how to add a tile for your Huawei Sun2000 inverter to the Venus OS overview screen (the main tiles display).

## Installation Steps

### Method 1: Automatic Installation (Recommended)

Run this command on your Venus OS device:

```bash
sh /data/dbus-huaweisun2000-pvinverter/gui/add_overview_tile.sh
```

### Method 2: Manual Installation

1. **Backup the original file:**
   ```bash
   cp /opt/victronenergy/gui/qml/OverviewTiles.qml /opt/victronenergy/gui/qml/OverviewTiles.qml.backup
   ```

2. **Add the tile component:**

   Edit `/opt/victronenergy/gui/qml/OverviewTiles.qml` and find the PV CHARGER tile section (around line 185-194). After the closing brace of the PV CHARGER tile, add:

   ```qml
   OverviewSolarInverter {
       width: 160
       height: bottomRow.height
   }
   ```

   The result should look like this:
   ```qml
   OverviewTile {
       id: pvChargerTile
       title: qsTr("PV CHARGER")
       width: 160
       height: bottomRow.height
       color: "#2cc36b"

       values: TileText {
           text: sys.pvCharger.power.format(0)
           font.pixelSize: 25
       }

       MbIcon {
           iconId: "overview-pv-charger-flow"
           anchors {
               top: parent.top
               right: parent.right
               margins: 5
           }
           visible: sys.pvCharger.power.valid
       }
   }

   OverviewSolarInverter {
       width: 160
       height: bottomRow.height
   }
   ```

3. **Restart the GUI:**
   ```bash
   svc -t /service/gui
   ```

## What This Tile Shows

The OverviewSolarInverter component will automatically detect your Huawei Sun2000 inverter and display:

- **Current Power Output**: Real-time power generation in Watts/kW
- **Total Energy**: Lifetime energy production (your current: 29.46 MWh!)
- **Inverter Status**: Running, Standby, or Error states
- **Visual Indicator**: Icon showing solar generation status

## Troubleshooting

### Tile Not Showing
- Make sure your inverter service is running: `svstat /service/dbus-huaweisun2000-pvinverter`
- Check if the inverter appears in dbus: `dbus -y com.victronenergy.pvinverter.sun2000`
- Verify the tile was added correctly: `grep -A 3 "OverviewSolarInverter" /opt/victronenergy/gui/qml/OverviewTiles.qml`

### Tile Shows No Data
- This is normal at night when the inverter is in standby mode
- During the day with sunlight, the tile should show current power output
- Total energy should always be visible (even at night)

### Reverting Changes
If you need to remove the tile:
```bash
cp /opt/victronenergy/gui/qml/OverviewTiles.qml.backup /opt/victronenergy/gui/qml/OverviewTiles.qml
svc -t /service/gui
```

## Technical Details

The `OverviewSolarInverter` component is a built-in Venus OS QML component that:
- Automatically scans for `com.victronenergy.pvinverter.*` services
- Displays aggregated data if multiple inverters are present
- Handles connection/disconnection gracefully
- Uses the same visual style as other overview tiles

This is more reliable than the generic PV INVERTER tiles because it reads directly from the inverter service instead of relying on aggregated system values.
