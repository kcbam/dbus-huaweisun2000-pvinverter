#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

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
import logging
import sys
import time
import os
import logging_config
from dbus.mainloop.glib import DBusGMainLoop
import dbus
from connector_modbus import ModbusDataCollector2000
from settings import HuaweiSUN2000Settings

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService


class DbusRunServices:
    def __init__(self, services_data, settings, logger):
        self.DBusServiceData = services_data
        self.settings = settings
        self.logger = logger
        self.trials = 0

    def run(self):
        GLib.timeout_add(self.settings.get('update_time_ms'), self._update)  # pause in ms before the next request
        self.logger.info('Connected to dbus, switching over to MainLoop and waiting for updates')
        self.logger.info('Enable DEBUG logging or use the "dbus-spy" command to inspect data updates on DBus if needed.')
        mainloop = GLib.MainLoop()
        mainloop.run()

    def _update(self):
        for dbus_service in self.DBusServiceData.values():
            try:
                data_collector = dbus_service['data']  # get the data collector function
                data_values = data_collector()  # call the data collector function to get the latest data
            except Exception as e:
                self.logger.critical("Data collector exception: " + str(e))
                sys.exit(0)  # Exit to force service restart...

            if data_values is None:
                self.logger.critical("TCP connection is probably lost. No data received. Retrying...")
                self.trials += 1
                if self.trials >= 5:
                    sys.exit(0)  # Exit to force service restart...
            else:
                self.trials = 0
                with dbus_service['service'] as s:  # get the dbus service object
                    try:
                        # Preserve previous status so we can log changes later
                        try:
                            old_status = s['/Status']
                            if old_status == '' or old_status is None:
                                old_status = 'unknown'
                        except KeyError:
                            old_status = None

                        # Update all the values in the dbus service with the ones we got from the inverter
                        for k, v in data_values.items():
                            self.logger.debug(f"Set {k} to {v}")
                            s[k] = v

                        # Log the status changes of the device, which shouldn't be too many and
                        # sometimes it's of value for the user to know.
                        if old_status is not None and s['/Status'] != old_status:
                            if s['/Status'] == '' or s['/Status'] is None:
                                s['/Status'] = 'unknown'
                            self.logger.info(f'Device status changed from {old_status} to {s["/Status"]}')

                        # increment UpdateIndex - to show that new data is available (and wrap)
                        s['/UpdateIndex'] = (s['/UpdateIndex'] + 1) % 256

                        # update lastupdate vars
                        self._lastUpdate = time.time()

                    except Exception as e:
                        self.logger.critical('Error at %s', '_update', exc_info=e)

        return True


class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)


class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)


def dbusconnection():
    return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()


def handlechangedvalue(path, value):
    return True  # accept the change


def get_version(logger):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'VERSION')
        with open(file_path, 'r') as file:
            version = file.readline().strip().split("v")[1]
            major = version.split('.')[0]
            minor = ''.join(version.split('.')[1:]).replace('.', '')
            return f"{major}.{minor}"
    except Exception as e:
        logger.error(f"Error reading VERSION file {file_path}: {e}")
        return '0.1'


def NewService(servicename, settings, logger, paths, devicedata, role='pvinverter'):

    serialnumber = devicedata['SN']
    productname = devicedata['Model']

    _dbusservice = VeDbusService(servicename, bus=dbusconnection(), register=False)

    # Create the management objects, as specified in the ccgx dbus-api document
    _dbusservice.add_path('/Mgmt/ProcessName', __file__ + '_' + role)
    _dbusservice.add_path('/Mgmt/ProcessVersion',
                          'Unkown version, and running on Python ' + platform.python_version())
    _dbusservice.add_path('/Mgmt/Connection', 'Modbus TCP')

    # Create the mandatory objects
    if role == 'pvinverter':
        instance = settings.get_vrm_instance()
    else:
        instance = settings.get_vrm_instance() + 1

    _dbusservice.add_path('/DeviceInstance', instance)
    _dbusservice.add_path('/ProductId', 0xFFFF)  # Unknown product
    _dbusservice.add_path('/ProductName', productname)
    if settings.get("custom_name") not in ["none", ""]:
        _dbusservice.add_path('/CustomName', settings.get("custom_name"))
    else:
        _dbusservice.add_path('/CustomName', productname)
    _dbusservice.add_path('/FirmwareVersion', get_version(logger))
    _dbusservice.add_path('/HardwareVersion', 0)
    _dbusservice.add_path('/Connected', 1, writeable=True)

    # Create the mandatory objects
    _dbusservice.add_path('/Latency', None)
    _dbusservice.add_path('/Role', role)
    _dbusservice.add_path('/Position', settings.get("position"))  # 0 = AC Input, 1 = AC-Out 1, AC-Out 2
    _dbusservice.add_path('/Serial', serialnumber)
    _dbusservice.add_path('/ErrorCode', 0)
    _dbusservice.add_path('/UpdateIndex', 0)
    _dbusservice.add_path('/StatusCode', 7)  # 0 = Startup, 7 = Running, 8 = Standby, 9 = Bootloading, 10 = Error

    for _path, _settings in paths.items():
        _dbusservice.add_path(
            _path, _settings['initial'], gettextcallback=_settings.get('textformat', lambda p, v: v), writeable=True,
            onchangecallback=handlechangedvalue)

    # For debugging
    for k, v in _dbusservice._dbusobjects.items():
        logger.debug(f"_dbusservice: {k}: Val: {v.GetValue()} Text: {v.GetText()}")

    return _dbusservice


def exit_mainloop(mainloop):
    mainloop.quit()


def main():
    formatter = logging.Formatter("(%(module)s.%(funcName)s) %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging_config.LOGGING)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    settings = HuaweiSUN2000Settings(logger)
    logger.info(f"VRM pvinverter instance: {settings.get_vrm_instance()}")
    logger.info(f"Settings: ModbusHost '{settings.get('modbus_host')}', ModbusPort '{settings.get('modbus_port')}', ModbusUnit '{settings.get('modbus_unit')}'")
    logger.info(f"Settings: CustomName '{settings.get('custom_name')}', Position '{settings.get('position')}', UpdateTimeMS '{settings.get('update_time_ms')}'")
    logger.info(f"Settings: PowerCorrectionFactor '{settings.get('power_correction_factor')}'")

    while "255" in settings.get("modbus_host"):
        # This catches the initial setting and allows the service to be installed without configuring it first
        logger.warning(f"Please configure the modbus host and other settings in the VenusOS GUI (current setting: {settings.get('modbus_host')})")
        # Running a mainloop means we'll be notified about config changes and exit in that case (which restarts the service)
        mainloop = GLib.MainLoop()
        mainloop.run()

    modbus = ModbusDataCollector2000(logger=logger,
                                     host=settings.get("modbus_host"),
                                     port=settings.get("modbus_port"),
                                     modbus_unit=settings.get("modbus_unit"),
                                     power_correction_factor=settings.get("power_correction_factor"),
                                     system_type=settings.get("system_type"))

    while True:
        staticdata = modbus.getStaticData()
        if staticdata is None:
            logger.error("Didn't receive static data from modbus, error is above. Sleeping 10 seconds before retrying.")
            # Again we sleep in the mainloop in order to pick up config changes
            mainloop = GLib.MainLoop()
            GLib.timeout_add(10000, exit_mainloop, mainloop)
            mainloop.run()
            continue
        else:
            logger.info("Static device data: " + str(staticdata))
            break

    try:
        logger.info("Starting up")

        # formatting
        def _kwh(p, v):
            return str(round(v, 2)) + ' kWh'

        def _a(p, v):
            return str(round(v, 1)) + ' A'

        def _w(p, v):
            return str(round(v, 1)) + ' W'

        def _v(p, v):
            return str(round(v, 1)) + ' V'

        def _hz(p, v):
            return f"{v:.4f}Hz"

        def _n(p, v):
            return f"{v:d}"

        if settings.get("system_type") == 1:
            dbuspath_inv = {
                '/Ac/Power': {'initial': 0, 'textformat': _w},
                '/Ac/Energy/Forward': {'initial': None, 'textformat': _kwh},
                #
                '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
                '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
                '/Ac/L1/Frequency': {'initial': None, 'textformat': _hz},
                '/Ac/L1/Energy/Forward': {'initial': None, 'textformat': _kwh},
                #
                '/Ac/MaxPower': {'initial': 20000, 'textformat': _w},
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
                '/Status': {'initial': ""},
            }

            dbuspath_meter = {
                '/DeviceType': {'initial': ""},
                '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh},  # energy bought from the grid
                '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh},  # energy sold to the grid
                '/Ac/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
                '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
                '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},
                '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
                '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
                '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
                '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
            }
        else:
            dbuspath_inv = {
                '/Ac/Power': {'initial': 0, 'textformat': _w},
                '/Ac/Energy/Forward': {'initial': None, 'textformat': _kwh},
                #
                '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
                '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
                '/Ac/L1/Frequency': {'initial': None, 'textformat': _hz},
                '/Ac/L1/Energy/Forward': {'initial': None, 'textformat': _kwh},
                #
                '/Ac/MaxPower': {'initial': 20000, 'textformat': _w},
                '/Ac/StatusCode': {'initial': 0, 'textformat': _n},
                '/Dc/Power': {'initial': 0, 'textformat': _w},
                '/Status': {'initial': ""},
            }

            dbuspath_meter = {
                '/DeviceType': {'initial': ""},
                '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh},  # energy bought from the grid
                '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh},  # energy sold to the grid
                '/Ac/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
                '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
                '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
            }

        DbusServices = {}

        inverter_service = NewService(servicename='com.victronenergy.pvinverter.sun2000',
                                      settings=settings,
                                      logger=logger,
                                      paths=dbuspath_inv,
                                      devicedata=staticdata,
                                      role='pvinverter')
        DbusServices['pvinverter'] = {'service': inverter_service, 'data': modbus.getInverterData}

        meter_service_grid = NewService(servicename='com.victronenergy.grid.ddsu666h',
                                        settings=settings,
                                        logger=logger,
                                        paths=dbuspath_meter,
                                        devicedata={'Model': 'DDSU666-H Meter', 'SN': '123456'},
                                        role='grid')

        meter_service_acload = NewService(servicename='com.victronenergy.acload.ddsu666h',
                                          settings=settings,
                                          logger=logger,
                                          paths=dbuspath_meter,
                                          devicedata={'Model': 'DDSU666-H Meter', 'SN': '123456'},
                                          role='acload')

        usemeter = settings.get("use_meter")
        if usemeter == 1:
            DbusServices['meter'] = {'service': meter_service_grid, 'data': modbus.getMeterData}
        elif usemeter == 2:
            DbusServices['meter'] = {'service': meter_service_acload, 'data': modbus.getMeterData}
        else:
            logger.info('No meter service created, as use_meter is set to %s', usemeter)

        for dbus_service in DbusServices.values():
            dbus_service['service'].register()

        run_services = DbusRunServices(
            services_data=DbusServices,
            settings=settings,
            logger=logger
        )
        run_services.run()

    except Exception as e:
        logger.critical('Error at %s', 'main', exc_info=e)


if __name__ == "__main__":
    main()
