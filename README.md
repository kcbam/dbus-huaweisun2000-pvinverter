# dbus-huaweisun2000-pvinverter

DBus driver for Victron Venus OS to integrate Huawei Sun2000 PV inverters with smart meter support.

## Features

✅ **Venus OS v3.67 Compatible** - Full support for latest Venus OS version
✅ **Smart Meter Integration** - Track grid import/export with DTSU666-H or similar meters
✅ **GUI-v1 & GUI-v2 Support** - Works with both Classic UI and New UI
✅ **Custom Overview Tile** - Real-time PV generation and grid flow display
✅ **VRM Portal Logging** - Historical data, graphs, and analytics
✅ **Comprehensive Data** - Per-phase voltage, current, power, and energy tracking
✅ **Easy Configuration** - All settings accessible via Venus OS GUI

## What This Driver Provides

### Inverter Data
- Real-time power output (AC and DC)
- Total lifetime energy production
- Per-phase data (L1, L2, L3): voltage, current, power, frequency
- Inverter status and error codes
- Device information (model, serial, firmware)

### Smart Meter Data (Optional)
If you have a DTSU666-H or compatible meter connected to your inverter via RS485:
- **Grid power flow** (positive = importing, negative = exporting)
- **Total energy imported** from grid (kWh bought)
- **Total energy exported** to grid (kWh sold)
- **Per-phase grid data** (L1, L2, L3)
- **Calculate self-consumption** and grid dependency

All data is logged to VRM Portal for historical tracking and analysis.

## Hardware Setup

### Required
- Victron Venus OS device (Cerbo GX, Raspberry Pi with Venus OS, etc.)
- Huawei Sun2000 inverter (tested with SUN2000-5KTL-L1)
- Network connection between Venus OS and inverter (WiFi or Ethernet)

### Optional (for Grid Tracking)
- DTSU666-H or DDSU666-H power meter
- Connected to inverter via RS485 (follows Huawei installation guide)

**Note:** The inverter's built-in WiFi can be used! No extra dongles needed - just connect Venus OS to the inverter's internal WiFi access point.

## Installation

### 1. Download and Install Driver

```bash
# SSH into your Venus OS device
ssh root@<your-venus-ip>

# Download the driver
wget https://github.com/detmin/dbus-huaweisun2000-pvinverter/archive/refs/heads/claude/venus-v3.67-breaking-changes-01BaBzZFNNoAivzvX9GyQDv3.zip -O huawei-driver.zip

# Extract to /data directory
unzip huawei-driver.zip -d /data

# Rename to expected directory name
mv /data/dbus-huaweisun2000-pvinverter-claude-venus-v3.67-breaking-changes-01BaBzZFNNoAivzvX9GyQDv3 /data/dbus-huaweisun2000-pvinverter

# Make installation script executable
chmod +x /data/dbus-huaweisun2000-pvinverter/install.sh

# Run installer
sh /data/dbus-huaweisun2000-pvinverter/install.sh

# Clean up
rm huawei-driver.zip
```

### 2. Configure Settings

Navigate to: **Settings → PV Inverters → Huawei SUN2000**

Configure:
- **Modbus Host**: Your inverter's IP address (default: 192.168.200.1)
- **Modbus Port**: Usually 6607
- **Modbus Unit ID**: Usually 0
- **Custom Name**: Optional display name
- **Position**: Where inverter is connected (AC Input 1/2 or AC Output)
- **Update Interval**: How often to poll data (default: 1000ms)

The service will automatically restart when you change settings.

### 3. Verify Installation

```bash
# Check service is running
svstat /service/dbus-huaweisun2000-pvinverter
# Should show: up (pid XXXX) XXX seconds

# Check inverter data is available
dbus -y com.victronenergy.pvinverter.sun2000 /Ac/Power GetValue
dbus -y com.victronenergy.pvinverter.sun2000 /Ac/Energy/Forward GetValue

# If you have a smart meter, check meter data
dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Power GetValue
dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Energy/Export GetValue
```

## GUI Overview Tile

Add a dedicated tile to your overview screen showing:
- Current PV generation
- Total lifetime energy production
- Grid import/export (if meter connected)

### Automatic Installation (Recommended)

```bash
sh /data/dbus-huaweisun2000-pvinverter/gui/add_overview_tile.sh
```

This script will:
- Copy the tile component to the GUI directory
- Find the correct location in OverviewTiles.qml
- Insert the tile automatically
- Restart the GUI

### Manual Installation

See `gui/overview_tile_instructions.md` for detailed manual installation steps.

## Optional: Detailed Inverter Page

A comprehensive detail page is available showing all inverter data.

**To install:**

1. Copy the detail page:
   ```bash
   cp /data/dbus-huaweisun2000-pvinverter/gui/PageHuaweiSUN2000Details.qml /opt/victronenergy/gui/qml/
   ```

2. Add menu entry to `/opt/victronenergy/gui/qml/PageMain.qml` - find the `model: VisibleItemModel {` line and add:
   ```qml
   MbSubMenu {
       description: qsTr("Huawei Inverter")
       subpage: Component { PageHuaweiSUN2000Details {} }
       show: pvinverterService.valid
       VBusItem { id: pvinverterService; bind: "com.victronenergy.pvinverter.sun2000/ProductName" }
   }
   ```

3. Restart GUI:
   ```bash
   svc -t /service/gui
   ```

## VRM Portal Integration

All data is automatically logged to the VRM Portal at https://vrm.victronenergy.com

**Data Upload Frequency:**
- Local updates: Every 1 second (configurable)
- VRM uploads: Every 15 minutes (typical)
- Historical graphs: 5-minute averages (permanent storage)

**What You'll See in VRM:**
- Real-time PV generation
- Grid import/export trends (if meter connected)
- Energy production statistics
- Self-consumption percentage
- Financial tracking (with energy pricing configured)

## Smart Meter Support

If your Huawei inverter has a DTSU666-H or DDSU666-H meter connected via RS485, the driver automatically detects and reads:

**Grid Data:**
- Grid power (positive = import, negative = export)
- Total energy imported (kWh bought from utility)
- Total energy exported (kWh sold to utility)
- Net energy balance

**Example:**
```bash
# Check if meter is detected
dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Status GetValue
# Returns 1.0 if meter is connected

# View grid power
dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Power GetValue
# Positive = importing, Negative = exporting

# Total energy counters
dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Energy/Import GetValue
dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Energy/Export GetValue
```

The overview tile automatically shows grid import/export when a meter is detected!

## Debugging

### Check Service Status
```bash
svstat /service/dbus-huaweisun2000-pvinverter
```

### View Live Logs
```bash
tail -f /var/log/dbus-huaweisun2000/current | tai64nlocal
```

### Test Modbus Connection
```bash
python /data/dbus-huaweisun2000-pvinverter/connector_modbus.py
```

### Restart Service
```bash
sh /data/dbus-huaweisun2000-pvinverter/restart.sh
```

### Stop/Start Service
```bash
svc -d /service/dbus-huaweisun2000-pvinverter  # Stop
svc -u /service/dbus-huaweisun2000-pvinverter  # Start
```

## Uninstallation

```bash
sh /data/dbus-huaweisun2000-pvinverter/uninstall.sh
rm -rf /data/dbus-huaweisun2000-pvinverter
```

**Note:** If you installed the optional overview tile or detail page, follow the manual cleanup instructions displayed by the uninstall script.

## Troubleshooting

### White Screen / GUI Crash
- **Fixed in Venus OS v3.67**: Driver now uses QtQuick 2 instead of QtQuick 1.1
- If you see a white screen, ensure you're using the latest version of this driver

### Inverter Not Detected
- Check IP address in Settings → PV Inverters → Huawei SUN2000
- Verify network connectivity: `ping <inverter-ip>`
- Check Modbus port: typically 6607
- Ensure inverter allows Modbus TCP connections

### Meter Data Not Showing
- Verify meter is physically connected to inverter via RS485
- Check meter status: `dbus -y com.victronenergy.pvinverter.sun2000 /Meter/Status GetValue`
- Should return 1.0 if meter is detected
- If returns 0 or None, check RS485 wiring and inverter settings

### Service Keeps Restarting
- Run manually to see errors: `python /data/dbus-huaweisun2000-pvinverter/dbus-huaweisun2000-pvinverter.py`
- Check logs: `tail -f /var/log/dbus-huaweisun2000/current | tai64nlocal`
- Verify Modbus connection works: Try connector_modbus.py test script

### DBus "NoReply" Errors in GUI Logs
If you see errors like `QDBusError("org.freedesktop.DBus.Error.NoReply"...)` for `com.victronenergy.grid.huawei_meter`:

**Cause:** You upgraded from an older version that used a separate grid meter service. That service no longer exists - meter data is now integrated into the pvinverter service.

**Fix:**
```bash
# Run the cleanup script to remove the old service
sh /data/dbus-huaweisun2000-pvinverter/cleanup-old-grid-service.sh

# Restart the GUI to clear the errors
svc -t /service/gui
```

After cleanup, all meter data will be available on the main service:
- `com.victronenergy.pvinverter.sun2000/Meter/Power`
- `com.victronenergy.pvinverter.sun2000/Meter/Energy/Import`
- `com.victronenergy.pvinverter.sun2000/Meter/Energy/Export`

## Technical Details

### Supported Venus OS Versions
- Venus OS v3.67 (tested)
- Venus OS v3.x (should work)
- Older versions may require GUI-v1 only

### GUI Versions
- **GUI-v1 (Classic UI)**: Full support with custom tiles and pages
- **GUI-v2 (New UI)**: Settings page support (WebAssembly variant cannot add custom pages)

### Modbus Communication
- Protocol: Modbus TCP
- Default Port: 6607
- Unit ID: 0 (typically)
- Supported Registers: Inverter equipment registers + Meter equipment registers

### DBus Paths
All data exposed via: `com.victronenergy.pvinverter.sun2000`

**Inverter Paths:**
- `/Ac/Power` - Current AC power output (W)
- `/Ac/Energy/Forward` - Total lifetime energy (kWh)
- `/Ac/L1/Power`, `/Ac/L2/Power`, `/Ac/L3/Power` - Per-phase power
- `/Ac/L1/Voltage`, `/Ac/L1/Current` - Per-phase voltage & current
- `/Dc/Power` - DC input power
- `/Status` - Inverter status text

**Meter Paths** (if connected):
- `/Meter/Power` - Grid power (W, +import/-export)
- `/Meter/Energy/Import` - Total imported energy (kWh)
- `/Meter/Energy/Export` - Total exported energy (kWh)
- `/Meter/L1/Power`, `/Meter/L2/Power`, `/Meter/L3/Power` - Per-phase grid power

## Contributing

Contributions are welcome! Please test thoroughly on your hardware before submitting pull requests.

## Credits

**Contributors:**
- DenkBrettl (original version)
- Community contributors

**Based on:**
- Modified version of https://github.com/olivergregorius/sun2000_modbus

**Inspired by:**
- https://github.com/RalfZim/venus.dbus-fronius-smartmeter
- https://github.com/fabian-lauer/dbus-shelly-3em-smartmeter
- https://github.com/victronenergy/velib_python

## License

Open source - use and modify as needed. No warranty provided.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
