#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

from enum import Enum
from . import datatypes
from . import mappings
from .registers import Register, AccessType


# Map the correct inverter register class based on the modbus version
class InverterRegister:

    @staticmethod
    def get(modbus_version: str):
        mapping = {
            "V1": InverterRegisterV1,
            "V2": InverterRegisterV2,
            "V3": InverterRegisterV3,
        }
        _class = mapping.get(modbus_version.upper())
        if not _class:
            _class = InverterRegisterV3
        return _class


# Not clear whether this is needed, might be removed in the future if not used.
class InverterRegisterV1(Enum):
    pass


# Version 2.0 (Older Models): Some older SUN2000 models (e.g., KTL-M0, some L1 models;
# models without any suffix, using Modbus RTU and connected to a SmartLogger)
# use a slightly different register map, often referred to as "Solar Inverter Modbus
# Interface Definitions V2.0".
class InverterRegisterV2(Enum):
    pass


# Version 3.0 (Latest Standard): Most modern SUN2000-KTL-M1/L1/M2/M3 models follow the
# "Solar Inverter Modbus Interface Definitions V3.0".
class InverterRegisterV3(Enum):
    Model = Register(30000, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None)
    SN = Register(30015, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None)
    PN = Register(30025, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None)
    ModelID = Register(30070, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    NumberOfPVStrings = Register(30071, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    NumberOfMPPTrackers = Register(30072, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    RatedPower = Register(30073, 2, datatypes.DataType.UINT32_BE, 1, "W", AccessType.RO, None)
    MaximumActivePower = Register(30075, 2, datatypes.DataType.UINT32_BE, 1, "W", AccessType.RO, None)
    MaximumApparentPower = Register(30077, 2, datatypes.DataType.UINT32_BE, 1000, "kVA", AccessType.RO, None)
    MaximumReactivePowerFedToTheGrid = Register(30079, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RO, None)
    MaximumReactivePowerAbsorbedFromTheGrid = Register(30081, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RO, None)
    State1 = Register(32000, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None)
    State2 = Register(32002, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None)
    State3 = Register(32003, 2, datatypes.DataType.BITFIELD32, None, None, AccessType.RO, None)
    Alarm1 = Register(32008, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None)
    Alarm2 = Register(32009, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None)
    Alarm3 = Register(32010, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None)
    PV1Voltage = Register(32016, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV1Current = Register(32017, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV2Voltage = Register(32018, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV2Current = Register(32019, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV3Voltage = Register(32020, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV3Current = Register(32021, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV4Voltage = Register(32022, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV4Current = Register(32023, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV5Voltage = Register(32024, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV5Current = Register(32025, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV6Voltage = Register(32026, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV6Current = Register(32027, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV7Voltage = Register(32028, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV7Current = Register(32029, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV8Voltage = Register(32030, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV8Current = Register(32031, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV9Voltage = Register(32032, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV9Current = Register(32033, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV10Voltage = Register(32034, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV10Current = Register(32035, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV11Voltage = Register(32036, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV11Current = Register(32037, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV12Voltage = Register(32038, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV12Current = Register(32039, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV13Voltage = Register(32040, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV13Current = Register(32041, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV14Voltage = Register(32042, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV14Current = Register(32043, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV15Voltage = Register(32044, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV15Current = Register(32045, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV16Voltage = Register(32046, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV16Current = Register(32047, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV17Voltage = Register(32048, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV17Current = Register(32049, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV18Voltage = Register(32050, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV18Current = Register(32051, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV19Voltage = Register(32052, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV19Current = Register(32053, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV20Voltage = Register(32054, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV20Current = Register(32055, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV21Voltage = Register(32056, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV21Current = Register(32057, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV22Voltage = Register(32058, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV22Current = Register(32059, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV23Voltage = Register(32060, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV23Current = Register(32061, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    PV24Voltage = Register(32062, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None)
    PV24Current = Register(32063, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None)
    InputPower = Register(32064, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    LineVoltageBetweenPhasesAAndB = Register(32066, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None)
    LineVoltageBetweenPhasesBAndC = Register(32067, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None)
    LineVoltageBetweenPhasesCAndA = Register(32068, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None)
    PhaseAVoltage = Register(32069, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None)
    PhaseBVoltage = Register(32070, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None)
    PhaseCVoltage = Register(32071, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None)
    PhaseACurrent = Register(32072, 2, datatypes.DataType.INT32_BE, 1000, "A", AccessType.RO, None)
    PhaseBCurrent = Register(32074, 2, datatypes.DataType.INT32_BE, 1000, "A", AccessType.RO, None)
    PhaseCCurrent = Register(32076, 2, datatypes.DataType.INT32_BE, 1000, "A", AccessType.RO, None)
    PeakActivePowerOfCurrentDay = Register(32078, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    ActivePower = Register(32080, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    ReactivePower = Register(32082, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RO, None)
    PowerFactor = Register(32084, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RO, None)
    GridFrequency = Register(32085, 1, datatypes.DataType.UINT16_BE, 100, "Hz", AccessType.RO, None)
    Efficiency = Register(32086, 1, datatypes.DataType.UINT16_BE, 100, "%", AccessType.RO, None)
    InternalTemperature = Register(32087, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None)
    InsulationResistance = Register(32088, 1, datatypes.DataType.UINT16_BE, 1000, "MOhm", AccessType.RO, None)
    DeviceStatus = Register(32089, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, mappings.DeviceStatus)
    FaultCode = Register(32090, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    StartupTime = Register(32091, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None)
    ShutdownTime = Register(32093, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None)
    AccumulatedEnergyYield = Register(32106, 2, datatypes.DataType.UINT32_BE, 100, "kWh", AccessType.RO, None)
    DailyEnergyYield = Register(32114, 2, datatypes.DataType.UINT32_BE, 100, "kWh", AccessType.RO, None)
    ActiveAdjustmentMode = Register(35300, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    ActiveAdjustmentValue = Register(35302, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None)
    ActiveAdjustmentCommand = Register(35303, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    ReactiveAdjustmentMode = Register(35304, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    ReactiveAdjustmentValue = Register(35305, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None)
    ReactiveAdjustmentCommand = Register(35307, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    PowerMeterCollectionActivePower = Register(37113, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    TotalNumberOfOptimizers = Register(37200, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    NumberOfOnlineOptimizers = Register(37201, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    FeatureData = Register(37202, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    SystemTime = Register(40000, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RW, None)
    QUCharacteristicCurveMode = Register(40037, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None)
    QUDispatchTriggerPower = Register(40038, 1, datatypes.DataType.UINT16_BE, 1, "%", AccessType.RW, None)
    FixedActivePowerDeratedInKW = Register(40120, 1, datatypes.DataType.UINT16_BE, 10, "kW", AccessType.RW, None)
    ReactivePowerCompensationInPF = Register(40122, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RW, None)
    ReactivePowerCompensationQS = Register(40123, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RW, None)
    ActivePowerPercentageDerating = Register(40125, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RW, None)
    FixedActivePowerDeratedInW = Register(40126, 2, datatypes.DataType.UINT32_BE, 1, "W", AccessType.RW, None)
    ReactivePowerCompensationAtNight = Register(40129, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RW, None)
    CosPhiPPnCharacteristicCurve = Register(40133, 21, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None)
    QUCharacteristicCurve = Register(40154, 21, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None)
    PFUCharacteristicCurve = Register(40175, 21, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None)
    ReactivePowerAdjustmentTime = Register(40196, 1, datatypes.DataType.UINT16_BE, 1, "s", AccessType.RW, None)
    QUPowerPercentageToExitScheduling = Register(40198, 1, datatypes.DataType.UINT16_BE, 1, "%", AccessType.RW, None)
    # Startup = Register(40200, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.WO, None) # disabled because not readable (AccessType.WO)
    # Shutdown = Register(40201, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.WO, None) # disabled because not readable (AccessType.WO)
    GridCode = Register(42000, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None)
    ReactivePowerChangeGradient = Register(42015, 2, datatypes.DataType.UINT32_BE, 1000, "%/s", AccessType.RW, None)
    ActivePowerChangeGradient = Register(42017, 2, datatypes.DataType.UINT32_BE, 1000, "%/s", AccessType.RW, None)
    ScheduleInstructionValidDuration = Register(42019, 2, datatypes.DataType.UINT32_BE, 1, "s", AccessType.RW, None)
    TimeZone = Register(43006, 1, datatypes.DataType.INT16_BE, 1, "min", AccessType.RW, None)
