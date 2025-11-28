#!/usr/bin/env python3

"""
DBus service for Huawei inverter's connected grid meter (DTSU666-H)
Exposes grid import/export data as a separate com.victronenergy.grid service
so VRM Portal can properly track consumption and grid flow.
"""

from gi.repository import GLib
import platform
import logging
import sys
import time
import os
import config
from dbus.mainloop.glib import DBusGMainLoop
from connector_modbus import ModbusDataCollector2000Delux
from settings import HuaweiSUN2000Settings

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService


class DbusGridMeterService:
    def __init__(self, servicename, settings, paths, data_connector, serialnumber='DTSU666'):
        self._dbusservice = VeDbusService(servicename)
        self._data_connector = data_connector

        logging.debug("%s /DeviceInstance = %d" % (servicename, settings.get_vrm_instance() + 1))

        # Create the management objects
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion',
                                   'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', 'Huawei Inverter Modbus TCP')

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', settings.get_vrm_instance() + 1)
        self._dbusservice.add_path('/ProductId', 0)
        self._dbusservice.add_path('/ProductName', 'Grid Meter (via Huawei)')
        self._dbusservice.add_path('/CustomName', 'Grid Meter')
        self._dbusservice.add_path('/FirmwareVersion', 1.0)
        self._dbusservice.add_path('/HardwareVersion', 0)
        self._dbusservice.add_path('/Connected', 1)

        self._dbusservice.add_path('/Latency', None)
        self._dbusservice.add_path('/Role', 'grid')
        self._dbusservice.add_path('/Serial', serialnumber)
        self._dbusservice.add_path('/ErrorCode', 0)
        self._dbusservice.add_path('/UpdateIndex', 0)

        # Add all paths
        for _path, _settings in paths.items():
            self._dbusservice.add_path(
                _path, _settings['initial'], gettextcallback=_settings.get('textformat', lambda p, v: v), writeable=True,
                onchangecallback=self._handlechangedvalue)

        GLib.timeout_add(settings.get('update_time_ms'), self._update)

    def _update(self):
        with self._dbusservice as s:
            try:
                # Get meter data
                meter_data = self._data_connector.getMeterData()

                if meter_data is not None:
                    # Map meter paths to grid paths with proper naming
                    path_mapping = {
                        '/Meter/Power': '/Ac/Power',
                        '/Meter/Energy/Import': '/Ac/Energy/Forward',  # Energy FROM grid
                        '/Meter/Energy/Export': '/Ac/Energy/Reverse',  # Energy TO grid
                        '/Meter/L1/Voltage': '/Ac/L1/Voltage',
                        '/Meter/L2/Voltage': '/Ac/L2/Voltage',
                        '/Meter/L3/Voltage': '/Ac/L3/Voltage',
                        '/Meter/L1/Current': '/Ac/L1/Current',
                        '/Meter/L2/Current': '/Ac/L2/Current',
                        '/Meter/L3/Current': '/Ac/L3/Current',
                        '/Meter/L1/Power': '/Ac/L1/Power',
                        '/Meter/L2/Power': '/Ac/L2/Power',
                        '/Meter/L3/Power': '/Ac/L3/Power',
                        '/Meter/Frequency': '/Ac/Frequency',
                    }

                    for meter_path, grid_path in path_mapping.items():
                        if meter_path in meter_data and grid_path in s:
                            value = meter_data[meter_path]
                            logging.info(f"set {grid_path} to {value}")
                            s[grid_path] = value

                    # Calculate total current and voltage (average of phases)
                    if '/Ac/L1/Current' in s and '/Ac/L2/Current' in s and '/Ac/L3/Current' in s:
                        s['/Ac/Current'] = (s['/Ac/L1/Current'] + s['/Ac/L2/Current'] + s['/Ac/L3/Current']) / 3.0

                    if '/Ac/L1/Voltage' in s and '/Ac/L2/Voltage' in s and '/Ac/L3/Voltage' in s:
                        s['/Ac/Voltage'] = (s['/Ac/L1/Voltage'] + s['/Ac/L2/Voltage'] + s['/Ac/L3/Voltage']) / 3.0

                    # increment UpdateIndex
                    s['/UpdateIndex'] = (s['/UpdateIndex'] + 1) % 256
                    s['/Connected'] = 1
                else:
                    # No meter data available
                    s['/Connected'] = 0

                # update lastupdate vars
                self._lastUpdate = time.time()

            except Exception as e:
                logging.critical('Error at %s', '_update', exc_info=e)
                s['/Connected'] = 0

        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=config.LOGGING,
                        handlers=[
                            logging.StreamHandler()
                        ])

    DBusGMainLoop(set_as_default=True)

    settings = HuaweiSUN2000Settings()
    logging.info(f"Grid Meter instance: {settings.get_vrm_instance() + 1}")
    logging.info(f"Settings: ModbusHost '{settings.get('modbus_host')}', ModbusPort '{settings.get('modbus_port')}', ModbusUnit '{settings.get('modbus_unit')}'")

    while "255" in settings.get("modbus_host"):
        logging.warning(f"Please configure the modbus host first (current setting: {settings.get('modbus_host')})")
        mainloop = GLib.MainLoop()
        mainloop.run()

    modbus = ModbusDataCollector2000Delux(host=settings.get("modbus_host"),
                                          port=settings.get("modbus_port"),
                                          modbus_unit=settings.get("modbus_unit"),
                                          power_correction_factor=settings.get("power_correction_factor"))

    # Check if meter is available
    meter_data = modbus.getMeterData()
    if meter_data is None:
        logging.error("No grid meter detected. This service requires a DTSU666-H or similar meter connected to the inverter via RS485.")
        logging.error("The inverter driver will still work, but grid import/export data will not be available in VRM.")
        sys.exit(1)

    logging.info("Grid meter detected! Starting DBus service...")

    try:
        # formatting
        _kwh = lambda p, v: (str(round(v, 2)) + ' kWh')
        _a = lambda p, v: (str(round(v, 1)) + ' A')
        _w = lambda p, v: (str(round(v, 1)) + ' W')
        _v = lambda p, v: (str(round(v, 1)) + ' V')
        _hz = lambda p, v: f"{v:.4f}Hz"

        dbuspath = {
            # Grid power (negative = importing, positive = exporting from grid perspective)
            '/Ac/Power': {'initial': 0, 'textformat': _w},
            '/Ac/Current': {'initial': 0, 'textformat': _a},
            '/Ac/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/Frequency': {'initial': None, 'textformat': _hz},

            # Energy counters
            '/Ac/Energy/Forward': {'initial': None, 'textformat': _kwh},  # Imported from grid
            '/Ac/Energy/Reverse': {'initial': None, 'textformat': _kwh},  # Exported to grid

            # Per-phase data
            '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},

            '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},

            '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
        }

        grid_meter = DbusGridMeterService(
            servicename='com.victronenergy.grid.huawei_meter',
            settings=settings,
            paths=dbuspath,
            data_connector=modbus
        )

        logging.info('Connected to dbus, and switching over to GLib.MainLoop()')
        mainloop = GLib.MainLoop()
        mainloop.run()
    except Exception as e:
        logging.critical('Error at %s', 'main', exc_info=e)


if __name__ == "__main__":
    main()
