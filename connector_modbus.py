from sun2000_modbus import inverter
from sun2000_modbus import registers

from dbus.mainloop.glib import DBusGMainLoop

from settings import HuaweiSUN2000Settings

class ModbusDataCollector2000Delux:
    def __init__(self, host='192.168.200.1', port=6607, modbus_unit=0, power_correction_factor=0.995):
        self.invSun2000 = inverter.Sun2000(host=host, port=port, modbus_unit=modbus_unit)
        self.power_correction_factor = power_correction_factor

    def getData(self):
        # the connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            print("Connection error Modbus TCP")
            return None

        data = {}

        dbuspath = {
            '/Ac/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.ActivePower},
            '/Ac/L1/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.APhaseActivePower},
            '/Ac/L1/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseACurrent},
            '/Ac/L1/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseAVoltage},
            '/Ac/L2/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.BPhaseActivePower},
            '/Ac/L2/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseBCurrent},
            '/Ac/L2/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseBVoltage},
            '/Ac/L3/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.CPhaseActivePower},
            '/Ac/L3/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseCCurrent},
            '/Ac/L3/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseCVoltage},
            '/Dc/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.InputPower},
            '/Ac/MaxPower': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.MaximumActivePower},
        }

        for k, v in dbuspath.items():
            s = v.get("sun2000")
            data[k] = self.invSun2000.read(s)


        state1 = self.invSun2000.read(registers.InverterEquipmentRegister.State1)
        # statuscode =
        # data['/Ac/StatusCode'] = statuscode

        energy_forward = self.invSun2000.read(registers.InverterEquipmentRegister.AccumulatedEnergyYield)
        data['/Ac/Energy/Forward'] = energy_forward
        # There is no Modbus register for the phases
        data['/Ac/L1/Energy/Forward'] = round(energy_forward/3.0, 2)
        data['/Ac/L2/Energy/Forward'] = round(energy_forward/3.0, 2)
        data['/Ac/L3/Energy/Forward'] = round(energy_forward/3.0, 2)

        freq = self.invSun2000.read(registers.InverterEquipmentRegister.GridFrequency)
        data['/Ac/L1/Frequency'] = freq
        data['/Ac/L2/Frequency'] = freq
        data['/Ac/L3/Frequency'] = freq

        cosphi = float(self.invSun2000.read((registers.InverterEquipmentRegister.PowerFactor)))
        data['/Ac/L1/Power'] = cosphi * float(data['/Ac/L1/Voltage']) * float(data['/Ac/L1/Current']) * self.power_correction_factor
        data['/Ac/L2/Power'] = cosphi * float(data['/Ac/L2/Voltage']) * float(data['/Ac/L2/Current']) * self.power_correction_factor
        data['/Ac/L3/Power'] = cosphi * float(data['/Ac/L3/Voltage']) * float(data['/Ac/L3/Current']) * self.power_correction_factor

        return data

    def getStaticData(self):
        # the connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            print("Connection error Modbus TCP")
            return None

        try:
            data={}
            data['SN'] = self.invSun2000.read(registers.InverterEquipmentRegister.SN)
            data['ModelID'] = self.invSun2000.read(registers.InverterEquipmentRegister.ModelID)
            data['Model'] = str(self.invSun2000.read_formatted(registers.InverterEquipmentRegister.Model)).replace('\0','')
            data['NumberOfPVStrings'] = self.invSun2000.read(registers.InverterEquipmentRegister.NumberOfPVStrings)
            data['NumberOfMPPTrackers'] = self.invSun2000.read(registers.InverterEquipmentRegister.NumberOfMPPTrackers)
            return  data

        except:
            print("Problem while getting static data modbus TCP")
            return None


## Just for testing ##
if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    settings = HuaweiSUN2000Settings()
    inverter = inverter.Sun2000(host=settings.get("modbus_host"), port=settings.get("modbus_port"), modbus_unit=settings.get("modbus_unit"))
    inverter.connect()
    if inverter.isConnected():

        attrs = (getattr(registers.InverterEquipmentRegister, name) for name in dir(registers.InverterEquipmentRegister))
        datata = dict()
        for f in attrs:
            if isinstance(f, registers.InverterEquipmentRegister):
                datata[f.name]=inverter.read_formatted(f)

        for k, v in datata.items():
            print(f"{k}: {v}")
