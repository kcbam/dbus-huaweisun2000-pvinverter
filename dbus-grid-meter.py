#!/usr/bin/env python3

"""
DBus service for Huawei inverter's connected grid meter (DTSU666-H)
Reads meter data from the PV inverter's DBus service and exposes it as a
separate com.victronenergy.grid service so VRM Portal can properly track
consumption and grid flow.

This service does NOT connect to Modbus directly - it reads from the
PV inverter service's /Meter/* paths to avoid connection conflicts.
"""

from gi.repository import GLib
import platform
import logging
import sys
import time
import os
import config
from dbus.mainloop.glib import DBusGMainLoop

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService
from ve_utils import get_vrm_portal_id
import dbus


class DbusGridMeterService:
    def __init__(self, servicename, pv_service_name, vrm_instance, update_time_ms):
        self._dbusservice = VeDbusService(servicename)
        self._pv_service_name = pv_service_name

        # Get system bus to read from PV inverter service
        self._dbusconn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

        logging.debug("%s /DeviceInstance = %d" % (servicename, vrm_instance))

        # Create the management objects
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion',
                                   'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', 'DBus from PV Inverter')

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', vrm_instance)
        self._dbusservice.add_path('/ProductId', 0)
        self._dbusservice.add_path('/ProductName', 'Grid Meter (via Huawei)')
        self._dbusservice.add_path('/CustomName', 'Grid Meter')
        self._dbusservice.add_path('/FirmwareVersion', 1.0)
        self._dbusservice.add_path('/HardwareVersion', 0)
        self._dbusservice.add_path('/Connected', 0)

        self._dbusservice.add_path('/Latency', None)
        self._dbusservice.add_path('/Role', 'grid')
        self._dbusservice.add_path('/Serial', 'DTSU666')
        self._dbusservice.add_path('/ErrorCode', 0)
        self._dbusservice.add_path('/UpdateIndex', 0)

        # formatting
        _kwh = lambda p, v: (str(round(v, 2)) + ' kWh')
        _a = lambda p, v: (str(round(v, 1)) + ' A')
        _w = lambda p, v: (str(round(v, 1)) + ' W')
        _v = lambda p, v: (str(round(v, 1)) + ' V')
        _hz = lambda p, v: f"{v:.4f}Hz"

        # Grid service paths
        grid_paths = {
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

        for _path, _settings in grid_paths.items():
            self._dbusservice.add_path(
                _path, _settings['initial'], gettextcallback=_settings.get('textformat', lambda p, v: v), writeable=True,
                onchangecallback=self._handlechangedvalue)

        GLib.timeout_add(update_time_ms, self._update)

    def _read_dbus_value(self, path, default=None):
        """Read a value from the PV inverter's DBus service"""
        try:
            pv_service = self._dbusconn.get_object(self._pv_service_name, path)
            return pv_service.GetValue()
        except dbus.exceptions.DBusException as e:
            logging.debug(f"Could not read {self._pv_service_name}{path}: {e}")
            return default
        except Exception as e:
            logging.debug(f"Error reading {self._pv_service_name}{path}: {e}")
            return default

    def _update(self):
        with self._dbusservice as s:
            try:
                # Check if PV service has meter data by checking meter status
                meter_status = self._read_dbus_value('/Meter/Status', default=0)

                if meter_status is None or meter_status == 0:
                    # No meter data available
                    s['/Connected'] = 0
                    logging.debug("No meter data available from PV inverter")
                    return True

                # Map meter paths to grid paths
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

                # Read values from PV service and update grid service
                for meter_path, grid_path in path_mapping.items():
                    value = self._read_dbus_value(meter_path)
                    if value is not None:
                        logging.debug(f"set {grid_path} to {value}")
                        s[grid_path] = value

                # Calculate total current and voltage (average of phases)
                if s['/Ac/L1/Current'] is not None and s['/Ac/L2/Current'] is not None and s['/Ac/L3/Current'] is not None:
                    s['/Ac/Current'] = (s['/Ac/L1/Current'] + s['/Ac/L2/Current'] + s['/Ac/L3/Current']) / 3.0

                if s['/Ac/L1/Voltage'] is not None and s['/Ac/L2/Voltage'] is not None and s['/Ac/L3/Voltage'] is not None:
                    s['/Ac/Voltage'] = (s['/Ac/L1/Voltage'] + s['/Ac/L2/Voltage'] + s['/Ac/L3/Voltage']) / 3.0

                # increment UpdateIndex
                s['/UpdateIndex'] = (s['/UpdateIndex'] + 1) % 256
                s['/Connected'] = 1

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

    # Wait for PV inverter service to be available
    pv_service_name = 'com.victronenergy.pvinverter.sun2000'
    logging.info(f"Waiting for PV inverter service ({pv_service_name}) to be available...")

    dbusconn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

    # Check if PV service exists
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            dbusconn.get_object(pv_service_name, '/')
            logging.info(f"PV inverter service found!")
            break
        except dbus.exceptions.DBusException:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error(f"PV inverter service not found after {max_retries} retries. Exiting.")
                sys.exit(1)
            logging.info(f"PV service not yet available, retrying in 2 seconds... ({retry_count}/{max_retries})")
            time.sleep(2)

    # Check if meter data is available
    try:
        meter_status_obj = dbusconn.get_object(pv_service_name, '/Meter/Status')
        meter_status = meter_status_obj.GetValue()
        if meter_status == 0:
            logging.error("No grid meter detected in PV inverter service.")
            logging.error("This service requires a DTSU666-H or similar meter connected to the inverter via RS485.")
            sys.exit(1)
        logging.info(f"Grid meter detected (status: {meter_status})! Starting DBus grid service...")
    except dbus.exceptions.DBusException as e:
        logging.error(f"Could not read meter status from PV service: {e}")
        logging.error("Make sure the PV inverter service is running and has meter support.")
        sys.exit(1)

    try:
        # Use VRM instance + 1 to avoid conflicts with PV inverter
        # Update time matches PV inverter (default 2000ms)
        grid_meter = DbusGridMeterService(
            servicename='com.victronenergy.grid.huawei_meter',
            pv_service_name=pv_service_name,
            vrm_instance=31,  # Grid meter instance (PV inverter uses 30 by default)
            update_time_ms=2000
        )

        logging.info('Grid meter service connected to dbus, switching to GLib.MainLoop()')
        mainloop = GLib.MainLoop()
        mainloop.run()
    except Exception as e:
        logging.critical('Error at %s', 'main', exc_info=e)


if __name__ == "__main__":
    main()
