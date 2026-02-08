#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

from enum import Enum

from . import datatypes


class AccessType(Enum):
    RO = "ro"
    RW = "rw"
    WO = "wo"


class Register:
    address: int
    quantity: int
    data_type: datatypes.DataType
    gain: float
    unit: str
    access_type: AccessType
    mapping: dict

    def __init__(self, address, quantity, data_type, gain, unit, access_type, mapping):
        self.address = address
        self.quantity = quantity
        self.data_type = data_type
        self.gain = gain
        self.unit = unit
        self.access_type = access_type
        self.mapping = mapping
