from sun2000_modbus import inverter
from sun2000_modbus import registers

from dbus.mainloop.glib import DBusGMainLoop

from settings import HuaweiSUN2000Settings
import logging

state1Readable = {
    1: "standby",
    2: "grid connected",
    4: "grid connected normaly",
    8: "grid connection with derating due to power rationing",
    16: "grid connection with derating due to internal causes of the solar inverter",
    32: "normal stop",
    64: "stop due to faults",
    128: "stop due to power",
    256: "shutdown",
    512: "spot check"
}
state2Readable = {
    1: "locking status (0:locked;1:unlocked)",
    2: "pv connection stauts (0:disconnected;1:conncted)",
    4: "grid connected normaly",
    8: "grid connection with derating due to power rationing",
    16: "grid connection with derating due to internal causes of the solar inverter",
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


class ModbusDataCollector2000Delux:
    def __init__(self, host='192.168.200.1', port=6607, modbus_unit=0, power_correction_factor=0.995):
        self.invSun2000 = inverter.Sun2000(host=host, port=port, modbus_unit=modbus_unit)
        self.power_correction_factor = power_correction_factor

    def getData(self):
        # Force disconnect any existing connection to ensure clean state
        if self.invSun2000.isConnected():
            logging.debug("Disconnecting existing connection before getData")
            self.invSun2000.disconnect()

        # Connect fresh for this read cycle
        if not self.invSun2000.connect():
            logging.error("Connection error Modbus TCP")
            return None

        logging.debug(f"Reading inverter data with modbus unit {self.invSun2000.modbus_unit}")

        data = {}

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

        try:
            for k, v in dbuspath.items():
                s = v.get("sun2000")
                data[k] = self.invSun2000.read(s)
        except Exception as e:
            logging.error(f"Error reading inverter registers: {e}")
            self.invSun2000.disconnect()
            return None

        state1 = self.invSun2000.read(registers.InverterEquipmentRegister.State1)
        state1_string = ";".join([val for key, val in state1Readable.items() if int(state1)&key>0])
        data['/Status'] = state1_string

        # data['/Ac/StatusCode'] = statuscode

        energy_forward = self.invSun2000.read(registers.InverterEquipmentRegister.AccumulatedEnergyYield)
        data['/Ac/Energy/Forward'] = energy_forward
        # There is no Modbus register for the phases
        data['/Ac/L1/Energy/Forward'] = round(energy_forward / 3.0, 2)
        data['/Ac/L2/Energy/Forward'] = round(energy_forward / 3.0, 2)
        data['/Ac/L3/Energy/Forward'] = round(energy_forward / 3.0, 2)

        freq = self.invSun2000.read(registers.InverterEquipmentRegister.GridFrequency)
        data['/Ac/L1/Frequency'] = freq
        data['/Ac/L2/Frequency'] = freq
        data['/Ac/L3/Frequency'] = freq

        cosphi = float(self.invSun2000.read((registers.InverterEquipmentRegister.PowerFactor)))
        data['/Ac/L1/Power'] = cosphi * float(data['/Ac/L1/Voltage']) * float(
            data['/Ac/L1/Current']) * self.power_correction_factor
        data['/Ac/L2/Power'] = cosphi * float(data['/Ac/L2/Voltage']) * float(
            data['/Ac/L2/Current']) * self.power_correction_factor
        data['/Ac/L3/Power'] = cosphi * float(data['/Ac/L3/Voltage']) * float(
            data['/Ac/L3/Current']) * self.power_correction_factor

        logging.debug(f"Successfully read inverter data")
        # Disconnect to ensure clean state for next cycle
        self.invSun2000.disconnect()
        return data

    def getMeterData(self):
        """Read smart meter data if available (DTSU666-H or similar connected via RS485)"""
        logging.debug("getMeterData() called")

        # Force disconnect any existing connection to ensure clean state
        if self.invSun2000.isConnected():
            logging.debug("Disconnecting existing connection before getMeterData")
            self.invSun2000.disconnect()

        if not self.invSun2000.connect():
            logging.error("Connection error Modbus TCP in getMeterData")
            return None

        try:
            meter_data = {}

            # Check if meter is connected
            meter_status = self.invSun2000.read(registers.MeterEquipmentRegister.MeterStatus)
            logging.debug(f"Meter status = {meter_status}")
            if meter_status is None or meter_status == 0:
                logging.debug(f"Returning None - meter_status is {meter_status}")
                return None  # No meter connected

            meter_data['/Meter/Status'] = meter_status
            meter_data['/Meter/Type'] = self.invSun2000.read(registers.MeterEquipmentRegister.MeterType)

            # Grid power (positive = importing, negative = exporting)
            meter_data['/Meter/Power'] = self.invSun2000.read(registers.MeterEquipmentRegister.ActivePower)

            # Total energy counters
            meter_data['/Meter/Energy/Import'] = self.invSun2000.read(registers.MeterEquipmentRegister.PositiveActiveElectricity)
            meter_data['/Meter/Energy/Export'] = self.invSun2000.read(registers.MeterEquipmentRegister.ReverseActivePower)

            # Per-phase voltages and currents
            meter_data['/Meter/L1/Voltage'] = self.invSun2000.read(registers.MeterEquipmentRegister.APhaseVoltage)
            meter_data['/Meter/L2/Voltage'] = self.invSun2000.read(registers.MeterEquipmentRegister.BPhaseVoltage)
            meter_data['/Meter/L3/Voltage'] = self.invSun2000.read(registers.MeterEquipmentRegister.CPhaseVoltage)

            meter_data['/Meter/L1/Current'] = self.invSun2000.read(registers.MeterEquipmentRegister.APhaseCurrent)
            meter_data['/Meter/L2/Current'] = self.invSun2000.read(registers.MeterEquipmentRegister.BPhaseCurrent)
            meter_data['/Meter/L3/Current'] = self.invSun2000.read(registers.MeterEquipmentRegister.CPhaseCurrent)

            # Per-phase power
            meter_data['/Meter/L1/Power'] = self.invSun2000.read(registers.MeterEquipmentRegister.APhaseActivePower)
            meter_data['/Meter/L2/Power'] = self.invSun2000.read(registers.MeterEquipmentRegister.BPhaseActivePower)
            meter_data['/Meter/L3/Power'] = self.invSun2000.read(registers.MeterEquipmentRegister.CPhaseActivePower)

            logging.info(f"Read phase powers: L1={meter_data.get('/Meter/L1/Power')}, L2={meter_data.get('/Meter/L2/Power')}, L3={meter_data.get('/Meter/L3/Power')}")

            # Grid frequency
            meter_data['/Meter/Frequency'] = self.invSun2000.read(registers.MeterEquipmentRegister.GridFrequency)

            # Single-phase system detection and correction
            # Some single-phase meters (like DTSU666-H in single-phase mode) report total power
            # correctly but return 0 or INT32_MAX (not available) for individual phase powers.
            # Detect this and correct it.
            total_power = meter_data.get('/Meter/Power', 0)
            l1_power = meter_data.get('/Meter/L1/Power', 0)
            l2_power = meter_data.get('/Meter/L2/Power', 0)
            l3_power = meter_data.get('/Meter/L3/Power', 0)

            logging.debug(f"Before single-phase check: Total={total_power}, L1={l1_power}, L2={l2_power}, L3={l3_power}")

            # Helper function to check if a value is invalid (None, zero, or INT32_MAX)
            def is_invalid_power(value):
                if value is None:
                    return True
                # Check for INT32_MAX and scaled versions (2147483647, 214748364.7, etc.)
                if abs(value) >= 214748364:
                    return True
                # Check for effectively zero
                if abs(value) < 1:
                    return True
                return False

            # If all phase powers are invalid but total power is significant
            if (total_power is not None and abs(total_power) > 1 and not is_invalid_power(total_power) and
                is_invalid_power(l1_power) and is_invalid_power(l2_power) and is_invalid_power(l3_power)):
                # Single-phase system: assign total power to L1
                meter_data['/Meter/L1/Power'] = total_power
                logging.info(f"Single-phase meter detected: Assigned total power {total_power}W to L1")

            logging.debug(f"Returning meter_data with {len(meter_data)} items")
            for k in sorted(meter_data.keys()):
                if 'Power' in k:
                    logging.debug(f"  {k} = {meter_data[k]}")

            # Disconnect to ensure clean state for next cycle
            self.invSun2000.disconnect()
            return meter_data

        except Exception as e:
            logging.error(f"Error reading meter data: {e}")
            self.invSun2000.disconnect()
            return None

    def getStaticData(self):
        # Force disconnect any existing connection to ensure clean state
        if self.invSun2000.isConnected():
            logging.debug("Disconnecting existing connection before getStaticData")
            self.invSun2000.disconnect()

        if not self.invSun2000.connect():
            logging.error("Connection error Modbus TCP in getStaticData")
            return None

        try:
            logging.debug(f"Reading static data with modbus unit {self.invSun2000.modbus_unit}")
            data = {}
            data['SN'] = self.invSun2000.read(registers.InverterEquipmentRegister.SN)
            data['ModelID'] = self.invSun2000.read(registers.InverterEquipmentRegister.ModelID)
            data['Model'] = str(self.invSun2000.read_formatted(registers.InverterEquipmentRegister.Model)).replace('\0',
                                                                                                                   '')
            data['NumberOfPVStrings'] = self.invSun2000.read(registers.InverterEquipmentRegister.NumberOfPVStrings)
            data['NumberOfMPPTrackers'] = self.invSun2000.read(registers.InverterEquipmentRegister.NumberOfMPPTrackers)

            logging.debug("Successfully read static data")
            # Disconnect to ensure clean state for next cycle
            self.invSun2000.disconnect()
            return data

        except Exception as e:
            logging.error(f"Problem while getting static data modbus TCP: {e}")
            self.invSun2000.disconnect()
            return None



## Just for testing ##
if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    settings = HuaweiSUN2000Settings()
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
            print(f"{k}: {v}")
