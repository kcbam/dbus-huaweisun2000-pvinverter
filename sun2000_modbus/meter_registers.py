#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

from enum import Enum
from . import datatypes
from . import mappings
from .registers import Register, AccessType


class MeterRegister(Enum):
    MeterType = Register(37125, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, mappings.MeterType)
    MeterStatus = Register(37100, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, mappings.MeterStatus)
    MeterModelDetectionResult = Register(37138, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, mappings.MeterModelDetectionResult)
    APhaseVoltage = Register(37101, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None)
    BPhaseVoltage = Register(37103, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None)
    CPhaseVoltage = Register(37105, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None)
    APhaseCurrent = Register(37107, 2, datatypes.DataType.INT32_BE, 100, "A", AccessType.RO, None)
    BPhaseCurrent = Register(37109, 2, datatypes.DataType.INT32_BE, 100, "A", AccessType.RO, None)
    CPhaseCurrent = Register(37111, 2, datatypes.DataType.INT32_BE, 100, "A", AccessType.RO, None)
    ActivePower = Register(37113, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    ReactivePower = Register(37115, 2, datatypes.DataType.INT32_BE, 1, "var", AccessType.RO, None)
    PowerFactor = Register(37117, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RO, None)
    GridFrequency = Register(37118, 1, datatypes.DataType.INT16_BE, 100, "Hz", AccessType.RO, None)
    PositiveActiveElectricity = Register(37119, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None)
    ReverseActivePower = Register(37121, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None)
    AccumulatedReactivePower = Register(37123, 2, datatypes.DataType.INT32_BE, 100, "kvar", AccessType.RO, None)
    ABLineVoltage = Register(37126, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None)
    BCLineVoltage = Register(37128, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None)
    CALineVoltage = Register(37130, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None)
    APhaseActivePower = Register(37132, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    BPhaseActivePower = Register(37134, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    CPhaseActivePower = Register(37136, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
