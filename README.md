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

## Venus OS v3.67 and GUI-v2 Support

This driver now supports **both GUI-v1 (Classic UI) and GUI-v2 (New UI)**. Venus OS v3.50 introduced the new GUI-v2, and v3.67 fully supports it. The installation script automatically detects which GUI version(s) are installed on your system and configures the appropriate interface.

- **GUI-v1 (Classic UI)**: Supported for backward compatibility with older Venus OS versions
- **GUI-v2 (New UI)**: Fully supported for Venus OS v3.50+ including v3.67

The installer will configure whichever GUI version is available on your system, or both if you have both installed.

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

## GUI Settings

You can find the settings in the Remote Console:

- **GUI-v1 (Classic UI)**: Settings → PV Inverters → Huawei SUN2000
- **GUI-v2 (New UI)**: Settings → PV Inverters → Huawei SUN2000

The settings page allows you to configure:
- Modbus Host IP address
- Modbus Port (default: 502)
- Modbus Unit ID
- Custom inverter name
- Position (AC Input 1/2 or AC Output)
- Update interval in milliseconds
- Power correction factor

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
