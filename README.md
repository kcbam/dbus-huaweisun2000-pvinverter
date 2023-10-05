# dbus-huaweisun2000-pvinverter
dbus driver for victron cerbo gx / venus os for huawei sun 2000 inverter


## Installation

1. Copy the files to the /data folder on your venus:

   - /data/etc/dbus-huaweisun2000/dbus-fronius-smartmeter.py
   - /data/etc/dbus-huaweisun2000/kill_me.sh
   - /data/etc/dbus-huaweisun2000/service/run

2. Set permissions for files:

`chmod 755 /data/etc/dbus-huaweisun2000/service/run`

`chmod 744 /data/etc/dbus-huaweisun2000/kill_me.sh`


3. Get two files from the [velib_python](https://github.com/victronenergy/velib_python) and install them on your venus:

   - /data/etc/dbus-huaweisun2000/vedbus.py
   - /data/etc/dbus-huaweisun2000/ve_utils.py

4. Add a symlink to the file /data/rc.local:

   `ln -s /data/etc/dbus-huaweisun2000/service /service/dbus-huawei-sun2000-pvinverter`

   Or if that file does not exist yet, store the file rc.local from this service on your Raspberry Pi as /data/rc.local .
   You can then create the symlink by just running rc.local:
  
   `rc.local`

   The daemon-tools should automatically start this service within seconds.


### Debugging

You can check the status of the service with svstat:

`svstat /service/dbus-huawei-sun2000-pvinverter`

It will show something like this:

`/service/dbus-huawei-sun2000-pvinverter: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/etc/dbus-huaweisun2000/dbus-huawei-sun2000-pvinverter.py`

and see if it throws any error messages.

If the script stops with the message

`dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.grid"`

it means that the service is still running or another service is using that bus name.

#### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`/data/etc/dbus-huaweisun2000/kill_me.sh`

The daemon-tools will restart the scriptwithin a few seconds.

# Thank you
this project is inspired by 
https://github.com/RalfZim/venus.dbus-fronius-smartmeter
