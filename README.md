# dbus-huaweisun2000-pvinverter
dbus driver for victron cerbo gx / venus os for huawei sun 2000 inverter

## Purpose

This script is intended to help integrate a Huawei Sun 2000 inverter into the Venus OS and thus also into the VRM portal. 

I use a Cerbo GX, which I have integrated via Ethernet in the house network. I used the WiFi of the device to connect to the internal WiFi of the Huawei Sun 2000. Attention: No extra dongle is necessary! You can use the integrated Wifi, which is actually intended for configuration with the Huawei app (Fusion App or Sun2000 App). The advantage is that no additional hardware needs to be purchased and the inverter does not need to be connected to the Internet.

To further use the data, the mqtt broker from Venus OS can be used.

## Installation

1. Copy the full project directory to the /data/etc folder on your venus:

   - /data/etc/dbus-sun2000-pvinverter/

   Info: The /data directory persists data on venus os devices while updating the firmware

2. Edit the config.ini file
    
3. Run install.sh
 
   `sh /data/etc/dbus-sun2000-pvinverter/install.sh`

### Debugging

You can check the status of the service with svstat:

`svstat /service/dbus-sun2000-pvinverter`

It will show something like this:

`/service/dbus-sun2000-pvinverter: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/etc/dbus-sun2000/dbus-sun2000-pvinverter.py`

Also useful:

`tail -f /var/log/dbus-sun2000/current | tai64nlocal`

#### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`/data/etc/dbus-sun2000/restart.sh`

#### Uninstall the script

Run

`/data/etc/dbus-sun2000/uninstall.sh`

`rm -r /data/etc/dbus-sun2000/`

# Thank you
## Used libraries
modified verion of https://github.com/olivergregorius/sun2000_modbus

## this project is inspired by 
https://github.com/RalfZim/venus.dbus-fronius-smartmeter
