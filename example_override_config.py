#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

class ConfigOverride:
    def adjust_settings(self, settings):
        # Modbus register definition version for the inverter. Huawei uses different register
        # definitions for different inverter models. The default is V3. The list and explanation
        # of the different versions can be found in the sun2000_modbus/inverter_registers.py file.
        settings["modbus_version"] = "V3"
        # IP address for the inverter
        settings["modbus_host"] = "192.168.200.1"
        # Modbus port for the inverter, typically 502 or 6607
        settings["modbus_port"] = 6607
        # Modbus unit for the inverter, most often 0, some models need 1.
        # If you use a SmartLogger, this is the Communication Addres or
        # Logical Address, depending on your configuration.
        settings["modbus_unit"] = 0
        # Custom name for the inverter. Product name will be used if "none"
        settings["custom_name"] = "none"
        # 0 = AC Input, 1 = AC-Out 1, 2 = AC-Out 2
        settings["position"] = 0
        # Update time in milliseconds
        settings["update_time_ms"] = 1000
        # Power Correction Factor override. The inverter will adapt its power generation to
        # the grid power factor and report it in its own data. This overrides the value that the
        # inverter reports, if the value is below 0.8, which indicates that it's not a sensible
        # reading.
        settings["pcf_override"] = 0.995
        # 0 = No, 1 = Yes, on Grid, 2 = Yes, on AC Out 2 (not implemented yet)
        settings["use_meter"] = 0
        # 0 = Single Phase, 1 = Three Phase
        settings["system_type"] = 0
