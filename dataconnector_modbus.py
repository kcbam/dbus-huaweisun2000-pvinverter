from sun2000_modbus import inverter
from sun2000_modbus import registers

class ModbusDataCollector2000Delux:
    def __init__(self, host='192.168.200.1', port=6607):
        self.invSun2000 = inverter.Sun2000(host=host, port=port)

    def isConnected(self):
        return

    def getData(self):
        if not self.invSun2000.isConnected():
            try:
                self.invSun2000.connect()
            except:
                print("Mist, Verbinden geht nicht!!")

        data = {}

        dbuspath = {
            '/Ac/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.ActivePower},
            '/Ac/Energy/Forward': {'initial': None,
                                   "sun2000": registers.InverterEquipmentRegister.AccumulatedEnergyYield},
            '/Ac/L1/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.APhaseActivePower},
            '/Ac/L1/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseACurrent},
            '/Ac/L1/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseAVoltage},
            # '/Ac/L1/Energy/Forward': {'initial': None, sun2000": registers.MeterEquipmentRegister.APha},
            '/Ac/L2/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.BPhaseActivePower},
            '/Ac/L2/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseBCurrent},
            '/Ac/L2/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseBVoltage},
            # '/Ac/L2/Energy/Forward': {'initial': None, sun2000": registers.InverterEquipmentRegister.},
            '/Ac/L3/Power': {'initial': 0, "sun2000": registers.MeterEquipmentRegister.CPhaseActivePower},
            '/Ac/L3/Current': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseCCurrent},
            '/Ac/L3/Voltage': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.PhaseCVoltage},
            '/Dc/Power': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.InputPower},
            # '/Ac/L3/Energy/Forward': {'initial': None, sun2000": registers.InverterEquipmentRegister.},
            '/Ac/MaxPower': {'initial': 0, "sun2000": registers.InverterEquipmentRegister.MaximumActivePower},
            # '/Ac/Position': {'initial': int(config['PV']['position']), sun2000": registers.InverterEquipmentRegister.},
        }

        for k, v in dbuspath.items():
            s = v.get("sun2000")
            data[k] = self.invSun2000.read(s)


        state1 = self.invSun2000.read(registers.InverterEquipmentRegister.State1)
        # statuscode =
        # data['/Ac/StatusCode'] = statuscode

        freq = self.invSun2000.read(registers.InverterEquipmentRegister.GridFrequency)
        data['/Ac/L1/Frequency'] = freq
        data['/Ac/L2/Frequency'] = freq
        data['/Ac/L3/Frequency'] = freq

        cosphi = float(self.invSun2000.read((registers.InverterEquipmentRegister.PowerFactor)))
        data['/Ac/L1/Power'] = cosphi * float(data['/Ac/L1/Voltage'] * float(data['/Ac/L1/Current']))
        data['/Ac/L2/Power'] = cosphi * float(data['/Ac/L2/Voltage'] * float(data['/Ac/L2/Current']))
        data['/Ac/L3/Power'] = cosphi * float(data['/Ac/L3/Voltage'] * float(data['/Ac/L3/Current']))

        return data

## Just for testing ##
if __name__ == "__main__":
    modbus = ModbusDataCollector2000Delux()

    inverter = inverter.Sun2000(host='192.168.200.1', port=6607)
    inverter.connect()
    if inverter.isConnected():
    #     input_power = inverter.read_formatted(registers.InverterEquipmentRegister.InputPower)
    #     print(input_power)
    #     activ_power = inverter.read_formatted(registers.InverterEquipmentRegister.ActivePower)
    #     print(f"Active Power: {activ_power}")
    #     print(f"A Phase Voltage InverterEquipmentReg: {inverter.read_formatted(registers.InverterEquipmentRegister.PhaseAVoltage)}")
    #     print(f"A Phase Voltage MeterEquipmentReg: {inverter.read_formatted(registers.MeterEquipmentRegister.APhaseVoltage)}")

        attrs = (getattr(registers.InverterEquipmentRegister, name) for name in dir(registers.InverterEquipmentRegister))
        datata = dict()
        for f in attrs:
            if isinstance(f, registers.InverterEquipmentRegister):
                datata[f.name]=inverter.read_formatted(f)

        for k, v in datata.items():
            print(f"{k}: {v}")