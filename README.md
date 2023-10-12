# dbus-huaweisun2000-pvinverter
dbus driver for victron cerbo gx / venus os for huawei sun 2000 inverter


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

and see if it throws any error messages.

If the script stops with the message

`dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.grid"`

it means that the service is still running or another service is using that bus name.

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
