from sun2000_modbus import inverter
from sun2000_modbus import registers

inverter = inverter.Sun2000(host='192.168.200.1', port=6607)
inverter.connect()
if inverter.isConnected():
    input_power = inverter.read_formatted(registers.InverterEquipmentRegister.InputPower)
    print(input_power)
    voltage1 = inverter.read_formatted(registers.InverterEquipmentRegister.PV1Voltage)
    print(voltage1)
    test = inverter.read_formatted(registers.InverterEquipmentRegister.DailyEnergyYield)
    print(test)
