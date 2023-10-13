#!/usr/bin/env python3

"""
A class to put a simple service on the dbus, according to victron standards, with constantly updating
paths. See example usage below. It is used to generate dummy data for other processes that rely on the
dbus. See files in dbus_vebus_to_pvinverter/test and dbus_vrm/test for other usage examples.

To change a value while testing, without stopping your dummy script and changing its initial value, write
to the dummy data via the dbus. See example.

https://github.com/victronenergy/dbus_vebus_to_pvinverter/tree/master/test
"""
from gi.repository import GLib
import platform
import argparse
import logging
import sys
import time
import os
import configparser
from dataconnector_modbus import ModbusDataCollector2000Delux

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService


class DbusSun2000Service:
    def __init__(self, servicename, deviceinstance, paths, data_connector, productname='Huawei Sun2000 PV-Inverter',
                 connection='Internal Wifi Modbus TCP' ):
        self._dbusservice = VeDbusService(servicename)
        self._paths = paths
        self._data_connector = data_connector

        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Most simple and short way to add an object with an initial value of 5.
        # self._dbusservice.add_path('/Ac/Power', value=1000, description='Total power', writeable=False)
        # self._dbusservice.add_path('/DeviceType', value=1000, description='Total power', writeable=False)
        # Add objects required by ve-api

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion',
                                   'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        # self._dbusservice.add_path('/ProductId', 1442184)  #hopefully free
        self._dbusservice.add_path('/ProductId', 41283 )  # hopefully free
        self._dbusservice.add_path('/ProductName', productname)
        self._dbusservice.add_path('/FirmwareVersion', 1.0)
        self._dbusservice.add_path('/HardwareVersion', 0)
        self._dbusservice.add_path('/Connected', 1, writeable=True)

        # Create the mandatory objects
        self._dbusservice.add_path('/Latency', None)
        self._dbusservice.add_path('/Role', "pvinverter")
        self._dbusservice.add_path('/Position', 0)  # 0 = AC Input, 1 = AC-Out 1, AC-Out 2
        self._dbusservice.add_path('/Serial', "X")
        self._dbusservice.add_path('/ErrorCode', 0)
        self._dbusservice.add_path('/UpdateIndex', 0)
        self._dbusservice.add_path('/StatusCode', 7)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)

        GLib.timeout_add(1000, self._update)  # pause 500ms before the next request


    def _update(self):
        with self._dbusservice as s:

            try:

                meter_data = self._data_connector.getData()

                for k, v in meter_data.items():
                    logging.info(f"set {k} to {v}")
                    s[k] = v


                # logging
                logging.debug("House Consumption (/Ac/Power): %s" % (s['/Ac/Power']))
                logging.debug("House Forward (/Ac/Energy/Forward): %s" % (s['/Ac/Energy/Forward']))
                logging.debug("---");

                # increment UpdateIndex - to show that new data is available an wrap
                s['/UpdateIndex'] = (s['/UpdateIndex'] + 1) % 256
                #
                # update lastupdate vars
                self._lastUpdate = time.time()

            except Exception as e:
                logging.critical('Error at %s', '_update', exc_info=e)

        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change


# === All code below is to simply run it from the commandline for debugging purposes ===

# It will created a dbus service called com.victronenergy.pvinverter.output.
# To try this on commandline, start this program in one terminal, and try these commands
# from another terminal:
# dbus com.victronenergy.pvinverter.output
# dbus com.victronenergy.pvinverter.output /Ac/Energy/Forward GetValue
# dbus com.victronenergy.pvinverter.output /Ac/Energy/Forward SetValue %20
#
# Above examples use this dbus client: http://code.google.com/p/dbus-tools/wiki/DBusCli
# See their manual to explain the % in %20

def main():
    # logging.basicConfig(level=logging.DEBUG)
    # configure logging
    print("Halle Welt!!!")
    config = configparser.ConfigParser()
    config.read(f"{(os.path.dirname(os.path.realpath(__file__)))}/config.ini")

    modbus = ModbusDataCollector2000Delux(port=6607) #TODO CONFIGFILE

    logging_level = config["SUN2000"]["Logging"].upper()
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level= logging.DEBUG, #TODO CON
                        handlers=[
                            logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                            #logging.FileHandler("/tmp/current.log"),

                            logging.StreamHandler()
                        ])
    try:
        logging.info("Start");

        from dbus.mainloop.glib import DBusGMainLoop
        # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
        DBusGMainLoop(set_as_default=True)

        # # formatting
        _kwh = lambda p, v: (str(round(v, 2)) + ' kWh')
        _a = lambda p, v: (str(round(v, 1)) + ' A')
        _w = lambda p, v: (str(round(v, 1)) + ' W')
        _v = lambda p, v: (str(round(v, 1)) + ' V')
        _hz = lambda p, v: f"{v:.4f}Hz"
        _n = lambda p, v: f"{v:i}"

        dbuspath = {
            '/Ac/Power': {'initial': 0, 'textformat': _w},
            '/Ac/Current': {'initial': 0, 'textformat': _a},
            '/Ac/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/Energy/Forward': {'initial': None, 'textformat': _kwh},

            '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/L1/Frequency': {'initial': None, 'textformat': _hz},
            '/Ac/L1/Energy/Forward': {'initial': None, 'textformat': _kwh},
            #
            '/Ac/MaxPower': {'initial': 20000, 'textformat': _w},
            # # '/Ac/Position': {'initial': int(config['PV']['position']), 'textformat': _n},
            '/Ac/StatusCode': {'initial': 0, 'textformat': _n},
            '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/L2/Frequency': {'initial': None, 'textformat': _hz},
            '/Ac/L2/Energy/Forward': {'initial': None, 'textformat': _kwh},
            '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/L3/Frequency': {'initial': None, 'textformat': _hz},
            '/Ac/L3/Energy/Forward': {'initial': None, 'textformat': _kwh},
            '/Dc/Power': {'initial': 0, 'textformat': _w},
        }

        pvac_output = DbusSun2000Service(
            servicename='com.victronenergy.pvinverter.sun2000',
            deviceinstance=int(config["SUN2000"]["DeviceInstance"]),
            paths=dbuspath,
            data_connector=modbus
        )

        logging.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
        mainloop = GLib.MainLoop()
        mainloop.run()
    # except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
    #     logging.critical('Error in main type %s', str(e))
    except Exception as e:
        logging.critical('Error at %s', 'main', exc_info=e)


if __name__ == "__main__":
    main()
