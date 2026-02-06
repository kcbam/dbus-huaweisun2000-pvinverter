#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

import logging

from sun2000_modbus import inverter
from sun2000_modbus import registers

from dbus.mainloop.glib import DBusGMainLoop

from settings import HuaweiSUN2000Settings

state1Readable = {
    1: "standby",
    2: "grid connected",
    4: "grid connected normally",
    8: "derating due to power rationing",
    16: "derating due to internal causes of the solar inverter",
    32: "normal stop",
    64: "stop due to faults",
    128: "stop due to power",
    256: "shutdown",
    512: "spot check"
}

state2Readable = {
    1: "locking status (0:locked;1:unlocked)",
    2: "pv connection status (0:disconnected;1:connected)",
    4: "grid connected normally",
    8: "derating due to power rationing",
    16: "derating due to internal causes of the solar inverter",
    32: "normal stop",
    64: "stop due to faults",
    128: "stop due to power",
    256: "shutdown",
    512: "spot check"
}

state3Readable = {
    1: "off-grid(0:on-grid;1:off-grid",
    2: "off-grid-switch(0:disable;1:enable)"
}

alert1Readable = {
    1: "",
    2: ""
}


class ModbusDataCollector2000:
    def __init__(self, logger, host='192.168.200.1', port=6607, modbus_unit=0, pcf_override=0.995, system_type=0):
        self.invSun2000 = inverter.Sun2000(logger=logger, host=host, port=port, modbus_unit=modbus_unit, timeout=20)
        self.pcf_override = pcf_override
        self.system_type = system_type

    def getInverterData(self):
        # the connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            print("Connection error Modbus TCP")
            return None

        data = {}

        if self.system_type == 1:
            # Three phase inverter
            dbuspath = {
                '/Ac/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.ActivePower},
                '/Ac/L1/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseACurrent},
                '/Ac/L1/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseAVoltage},
                '/Ac/L2/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseBCurrent},
                '/Ac/L2/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseBVoltage},
                '/Ac/L3/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseCCurrent},
                '/Ac/L3/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseCVoltage},
                '/Dc/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.InputPower},
                '/Ac/MaxPower': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.MaximumActivePower},
            }
        else:
            # Single phase inverter
            dbuspath = {
                '/Ac/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.ActivePower},
                '/Ac/L1/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseACurrent},
                '/Ac/L1/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseAVoltage},
                '/Dc/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.InputPower},
                '/Ac/MaxPower': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.MaximumActivePower},
            }

        for k, v in dbuspath.items():
            s = v.get("sun2000")
            data[k] = self.invSun2000.read(s)

        data['/Status'] = self.invSun2000.read_formatted(registers.InverterEquipmentRegister.DeviceStatus)

        # Matching the DeviceStatus code mapping to the
        # codes for 'pvinverter' from the Victron dbus manual
        # https://github.com/victronenergy/venus/wiki/dbus#pv-inverters
        # 0=Startup 0; 1=Startup 1; 2=Startup 2; 3=Startup 3;
        # 4=Startup 4; 5=Startup 5; 6=Startup 6; 7=Running;
        # 8=Standby; 9=Boot loading; 10=Error
        match data['/Status']:
            case "Starting":
                data['/StatusCode'] = 0
            case "On-grid":
                data['/StatusCode'] = 7
            case "Grid connection: power limited":
                data['/StatusCode'] = 7
            case "Grid connection: self-derating":
                data['/StatusCode'] = 7
            case "Shutdown: fault":
                data['/StatusCode'] = 10
            case "Shutdown: command":
                data['/StatusCode'] = 10
            case "Shutdown: OVGR":
                data['/StatusCode'] = 10
            case "Shutdown: communication disconnected":
                data['/StatusCode'] = 10
            case "Shutdown: power limited":
                data['/StatusCode'] = 10
            case "Shutdown: manual startup required":
                data['/StatusCode'] = 10
            case "Shutdown: DC switches disconnected":
                data['/StatusCode'] = 10
            case "Shutdown: rapid cutoff":
                data['/StatusCode'] = 10
            case "Shutdown: input underpowered":
                data['/StatusCode'] = 10
            case "Standby: no irradiation":
                data['/StatusCode'] = 8
            case _:
                data['/StatusCode'] = 7  # Let's put the default to "running" (7)

        energy_forward = self.invSun2000.read(registers.InverterEquipmentRegister.AccumulatedEnergyYield)
        data['/Ac/Energy/Forward'] = energy_forward

        cosphi = float(self.invSun2000.read((registers.InverterEquipmentRegister.PowerFactor)))
        # This is a sanity check, if the value is too low, it's probably wrong and we override it with the value
        # from the config
        if cosphi < 0.8:
            cosphi = self.pcf_override

        freq = self.invSun2000.read(registers.InverterEquipmentRegister.GridFrequency)

        # There is no Modbus register for the phases
        data['/Ac/L1/Energy/Forward'] = round(energy_forward / 3.0, 2)
        data['/Ac/L1/Frequency'] = freq
        data['/Ac/L1/Power'] = cosphi * float(data['/Ac/L1/Voltage']) * float(
            data['/Ac/L1/Current'])

        if self.system_type == 1:
            # Three phase inverter
            data['/Ac/L2/Energy/Forward'] = round(energy_forward / 3.0, 2)
            data['/Ac/L3/Energy/Forward'] = round(energy_forward / 3.0, 2)
            data['/Ac/L2/Frequency'] = freq
            data['/Ac/L3/Frequency'] = freq
            data['/Ac/L2/Power'] = cosphi * float(data['/Ac/L2/Voltage']) * float(data['/Ac/L2/Current'])
            data['/Ac/L3/Power'] = cosphi * float(data['/Ac/L3/Voltage']) * float(data['/Ac/L3/Current'])

        return data

    def getMeterData(self):
        # the connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            print("Connection error Modbus TCP")
            return None

        """ com.victronenergy.grid
        com.victronenergy.acload (when used as consumer to measure an acload)
        com.victronenergy.genset (when used as producer to measure a genset)

        /Ac/Energy/Forward     <- kWh  - bought energy (total of all phases)
        /Ac/Energy/Reverse     <- kWh  - sold energy (total of all phases)
        /Ac/Power              <- W    - total of all phases, real power
        /Ac/PowerFactor        <-      - total power factor

        /Ac/Current            <- A AC - Deprecated
        /Ac/Voltage            <- V AC - Deprecated

        /Ac/L1/Current         <- A AC
        /Ac/L1/Energy/Forward  <- kWh  - bought
        /Ac/L1/Energy/Reverse  <- kWh  - sold
        /Ac/L1/Power           <- W, real power
        /Ac/L1/PowerFactor     <- power factor
        /Ac/L1/Voltage         <- V AC
        /Ac/L2/*               <- same as L1
        /Ac/L3/*               <- same as L1
        /DeviceType
        /ErrorCode

        /IsGenericEnergyMeter  <- When an energy meter masquarades as a genset or acload, this is set to 1.
        """

        data = {}

        if self.system_type == 1:
            # Three phase meter
            dbuspath = {
                '/DeviceType': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.MeterType},
                '/Ac/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.ActivePower},
                '/Ac/L1/Current': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.APhaseCurrent},
                '/Ac/L1/Voltage': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.APhaseVoltage},
                '/Ac/L2/Current': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.BPhaseCurrent},
                '/Ac/L2/Voltage': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.BPhaseVoltage},
                '/Ac/L3/Current': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.CPhaseCurrent},
                '/Ac/L3/Voltage': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.CPhaseVoltage},
            }
        else:
            # Single phase meter
            dbuspath = {
                '/DeviceType': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.MeterType},
                '/Ac/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.ActivePower},
                '/Ac/L1/Current': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.APhaseCurrent},
                '/Ac/L1/Voltage': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.APhaseVoltage},
            }

        data['/Ac/Energy/Forward'] = self.invSun2000.read(registers.MeterEquipmentRegister.ActivePower) / 1000
        data['/Ac/Energy/Reverse'] = self.invSun2000.read(registers.MeterEquipmentRegister.ReverseActivePower) / 1000

        for k, v in dbuspath.items():
            s = v.get("sun2000")
            data[k] = self.invSun2000.read(s)

        cosphi = abs(float(self.invSun2000.read((registers.MeterEquipmentRegister.PowerFactor))))
        # This is a sanity check, if the value is too low, it's probably wrong and we override it with the value
        # from the config
        if cosphi < 0.8:
            cosphi = self.pcf_override

        data['/Ac/L1/Power'] = -1 * cosphi * float(data['/Ac/L1/Voltage']) * float(data['/Ac/L1/Current'])

        if self.system_type == 1:
            # Three phase meter
            data['/Ac/L2/Power'] = -1 * cosphi * float(data['/Ac/L2/Voltage']) * float(data['/Ac/L2/Current'])
            data['/Ac/L3/Power'] = -1 * cosphi * float(data['/Ac/L3/Voltage']) * float(data['/Ac/L3/Current'])

        return data

    def getStaticData(self):
        # The connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            self.logger.error("Error connecting to Modbus TCP")
            return None

        try:
            data = {}
            data['SN'] = self.invSun2000.read(registers.InverterEquipmentRegister.SN)
            data['ModelID'] = self.invSun2000.read(registers.InverterEquipmentRegister.ModelID)
            data['Model'] = str(self.invSun2000.read_formatted(registers.InverterEquipmentRegister.Model)).replace('\0', '')
            data['NumberOfPVStrings'] = self.invSun2000.read(registers.InverterEquipmentRegister.NumberOfPVStrings)
            data['NumberOfMPPTrackers'] = self.invSun2000.read(registers.InverterEquipmentRegister.NumberOfMPPTrackers)
            return data

        except Exception as e:
            self.logger.error("Error getting static data via Modbus TCP: " + str(e))
            return None


# For testing
if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    formatter = logging.Formatter("(%(module)s.%(funcName)s) %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    settings = HuaweiSUN2000Settings(logger)
    inverter = inverter.Sun2000(host=settings.get("modbus_host"), port=settings.get("modbus_port"),
                                modbus_unit=settings.get("modbus_unit"))
    inverter.connect()
    if inverter.isConnected():

        attrs = (getattr(registers.InverterEquipmentRegister, name) for name in
                 dir(registers.InverterEquipmentRegister))
        datata = dict()
        for f in attrs:
            if isinstance(f, registers.InverterEquipmentRegister):
                datata[f.name] = inverter.read_formatted(f)

        for k, v in datata.items():
            logger.debug(f"{k}: {v}")
