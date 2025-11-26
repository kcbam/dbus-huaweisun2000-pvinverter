# dbus-huaweisun2000-pvinverter

dbus driver for victron cerbo gx / venus os for huawei sun 2000 inverter

## Purpose

This script is intended to help integrate a Huawei Sun 2000 inverter into the Venus OS and thus also into the VRM
portal.

I use a Cerbo GX, which I have integrated via Ethernet in the house network. I used the WiFi of the device to connect to
the internal WiFi of the Huawei Sun 2000. Attention: No extra dongle is necessary! You can use the integrated Wifi,
which is actually intended for configuration with the Huawei app (Fusion App or Sun2000 App). The advantage is that no
additional hardware needs to be purchased and the inverter does not need to be connected to the Internet.

To further use the data, the mqtt broker from Venus OS can be used.

## Venus OS v3.67 and GUI Support

This driver supports **GUI-v1 (Classic UI)** which is used by Venus OS v3.67. The installation script automatically detects which GUI version is installed on your system and configures the appropriate interface.

### GUI Versions Explained

Venus OS has two GUI systems:

**GUI-v1 (Classic UI)** - QML-based interface
- Used for on-screen display (HDMI/touch screens)
- Fully customizable with QML files
- ✅ **Fully supported by this driver**
- Location: `/opt/victronenergy/gui/qml/`

**GUI-v2 (New UI)** - Modern interface with two variants:
1. **Native QML** (Cerbo GX, GX Touch devices):
   - Uses Qt6 and modern QML components
   - Customizable with QML files
   - Location: `/opt/victronenergy/gui-v2/`
   - ✅ **Supported by this driver** (for devices that have it)

2. **WebAssembly** (Browser Remote Console):
   - Compiled binary for web browsers
   - Cannot be customized (compiled application)
   - ❌ **Cannot add custom pages** (use dbus settings instead)

**For Raspberry Pi 4 (Venus OS v3.67):**
- On-screen display uses **GUI-v1** (Classic UI) ✅
- Remote Console uses **GUI-v2 WebAssembly** (browser only)
- Settings configured through GUI-v1 work across both interfaces

The installer will configure whichever GUI version is available on your system.

## Todo

- [ ] better logging
- [x] find out why the most values are missing in the view
- [x] repair modelname (custom name in config)
- [x] possibility to change settings via gui
- [ ] alarm, state
- [ ] more values: temperature, efficiency
- [ ] clean code

Cooming soon

## Installation

1. Copy the full project directory to the /data/etc folder on your venus:

    - /data/dbus-huaweisun2000-pvinverter/

   Info: The /data directory persists data on venus os devices while updating the firmware

   Easy way:
   ```
   wget https://github.com/kcbam/dbus-huaweisun2000-pvinverter/archive/refs/heads/main.zip
   unzip main.zip -d /data
   mv /data/dbus-huaweisun2000-pvinverter-main /data/dbus-huaweisun2000-pvinverter
   chmod a+x /data/dbus-huaweisun2000-pvinverter/install.sh
   rm main.zip
   ```


3. Edit the config.py file (not longer needed. Watch for Settings in the Remote Console.)

   `nano /data/dbus-huaweisun2000-pvinverter/config.py`

5. Check Modbus TCP Connection to gridinverter

   `python /data/dbus-huaweisun2000-pvinverter/connector_modbus.py`

6. Run install.sh

   `sh /data/dbus-huaweisun2000-pvinverter/install.sh`

## GUI Interface

### Settings Page

You can configure the driver in the Remote Console:

- **Path**: Settings → PV Inverters → Huawei SUN2000

Available settings:
- Modbus Host IP address
- Modbus Port (default: 502)
- Modbus Unit ID
- Custom inverter name
- Position (AC Input 1/2 or AC Output)
- Update interval in milliseconds
- Power correction factor

### Inverter Detail Page (Optional)

The repository includes an optional detailed inverter status page (`PageHuaweiSUN2000Details.qml`) that shows:
- Current status and power output
- Total energy production
- Per-phase data (L1, L2, L3) - voltage, current, power, frequency, energy
- DC power
- Device information (model, serial, firmware)

**To add this page to your main menu:**

1. Copy the detail page to the GUI directory:
   ```bash
   cp /data/dbus-huaweisun2000-pvinverter/gui/PageHuaweiSUN2000Details.qml /opt/victronenergy/gui/qml/
   ```

2. Edit `/opt/victronenergy/gui/qml/PageMain.qml` and add the menu entry. Find the line with `model: VisibleItemModel {` (around line 20) and add:
   ```qml
   MbSubMenu {
       description: qsTr("Huawei Inverter")
       subpage: Component { PageHuaweiSUN2000Details {} }
       show: pvinverterService.valid
       VBusItem { id: pvinverterService; bind: "com.victronenergy.pvinverter.sun2000/ProductName" }
   }
   ```

3. Restart the GUI:
   ```bash
   svc -t /service/gui
   ```

The "Huawei Inverter" menu item will now appear on the main menu when the inverter is connected.

### Debugging

You can check the status of the service with svstat:

`svstat /service/dbus-huaweisun2000-pvinverter`

It will show something like this:

`/service/dbus-huaweisun2000-pvinverter: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets
restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/dbus-huaweisun2000-pvinverter/dbus-huaweisun2000-pvinverter.py`

Also useful:

`tail -f /var/log/dbus-huaweisun2000/current | tai64nlocal`

### Stop the script

`svc -d /service/dbus-huaweisun2000-pvinverter`

### Start the script

`svc -u /service/dbus-huaweisun2000-pvinverter`


### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`sh /data/dbus-huaweisun2000-pvinverter/restart.sh`

## Uninstall the script

Run

   ```
sh /data/dbus-huaweisun2000-pvinverter/uninstall.sh
rm -r /data/dbus-huaweisun2000-pvinverter/
   ```

# Examples

![VRM-01](img/VRM-01.png)

![VRM-02](img/VRM-02.png)


# Thank you
## Contributers

DenkBrettl

## Used libraries

modified verion of https://github.com/olivergregorius/sun2000_modbus

## this project is inspired by

https://github.com/RalfZim/venus.dbus-fronius-smartmeter

https://github.com/fabian-lauer/dbus-shelly-3em-smartmeter.git

https://github.com/victronenergy/velib_python.git
