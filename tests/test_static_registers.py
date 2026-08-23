#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

"""Tests for reading unchanging registers only once.

Needs python-dbus, because connector_modbus imports the settings module. On a machine
without it these tests are skipped; they run on the Venus device itself.
"""

import pytest

pytest.importorskip("dbus", reason="connector_modbus imports the D-Bus settings module")

import connector_modbus
from sun2000_modbus import inverter_registers


class InverterStub:
    """Records the registers asked for in every cycle."""

    def __init__(self):
        self.requests = []

    def connect(self):
        return True

    def read_registers(self, registers):
        self.requests.append([register.name for register in registers])
        return {register: 55000.0 if register.name == "MaximumActivePower" else 1.0 for register in registers}

    def format_value(self, register, value, use_locale=False):
        return "On-grid"


@pytest.fixture
def collector():
    instance = connector_modbus.ModbusDataCollector2000.__new__(connector_modbus.ModbusDataCollector2000)
    instance.logger = LoggerStub()
    instance.pcf_override = 0.995
    instance.system_type = 1
    instance.this_inverter = inverter_registers.InverterRegister.get("V3")
    instance.static_registers = (instance.this_inverter.MaximumActivePower,)
    instance.static_values = {}
    instance.invSun2000 = InverterStub()
    return instance


class LoggerStub:
    def _ignore(self, message):
        pass

    debug = info = warning = error = critical = _ignore


def test_the_nameplate_rating_is_requested_once_and_then_reused(collector):
    cycles = [collector.getInverterData() for _ in range(3)]
    requests = collector.invSun2000.requests

    assert "MaximumActivePower" in requests[0]
    assert "MaximumActivePower" not in requests[1]
    assert "MaximumActivePower" not in requests[2]
    assert all(cycle["/Ac/MaxPower"] == 55000.0 for cycle in cycles)


def test_dropping_the_static_register_shortens_the_request_by_exactly_one(collector):
    collector.getInverterData()
    collector.getInverterData()
    requests = collector.invSun2000.requests

    assert len(requests[0]) - len(requests[1]) == 1


def test_the_other_values_keep_coming(collector):
    collector.getInverterData()
    cycle = collector.getInverterData()

    assert cycle["/Ac/Power"] == 1.0
    assert cycle["/Ac/L1/Voltage"] == 1.0
    assert cycle["/Status"] == "On-grid"
