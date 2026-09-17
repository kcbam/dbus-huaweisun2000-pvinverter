#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

"""Tests for the grouped block reads.

Run with `pytest`. Needs the same pymodbus the driver uses: `pip install pymodbus==2.5.3 pytest`.
"""

import struct
from enum import Enum

import pytest
from pymodbus.exceptions import ConnectionException, ModbusIOException

from sun2000_modbus import datatypes
from sun2000_modbus import inverter
from sun2000_modbus.registers import AccessType, Register


class SampleRegister(Enum):
    UINT16_WITH_GAIN = Register(100, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None)
    INT32_SIGNED = Register(101, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None)
    WITHOUT_GAIN = Register(103, 1, datatypes.DataType.UINT16_BE, None, None, AccessType.RO, None)
    TEXT = Register(104, 3, datatypes.DataType.STRING, None, None, AccessType.RO, None)
    FAR_AWAY = Register(200, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)


# Registers 100..106 as they would arrive from the inverter.
SAMPLE_PAYLOAD = b"".join(struct.pack(">H", word) for word in (2325, 0xFFFF, 0xFFFF - 999, 7)) + b"ABCDE\0"


def make_inverter():
    """A Sun2000 without a TCP connection. Tests replace the parts they exercise."""
    instance = inverter.Sun2000.__new__(inverter.Sun2000)
    instance.logger = LoggerSpy()
    instance.modbus_unit = 1
    instance.max_retries = 0
    instance.backoff_in_seconds = 0
    instance.backoff_factor = 1.0
    instance.block_read = True
    instance.rejected_groups = set()
    return instance


class LoggerSpy:
    def __init__(self):
        self.messages = []

    def _record(self, message):
        self.messages.append(str(message))

    debug = info = warning = error = critical = _record


class RangeStub:
    """Answers read_range from a fixed payload and records what was asked for."""

    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def __call__(self, start_address, quantity=0, end_address=0):
        self.calls.append((start_address, quantity))
        return self.payload


def test_read_block_asks_for_one_span_covering_all_registers():
    sun2000 = make_inverter()
    sun2000.read_range = RangeStub(SAMPLE_PAYLOAD)

    sun2000.read_block([SampleRegister.UINT16_WITH_GAIN, SampleRegister.TEXT])

    assert sun2000.read_range.calls == [(100, 7)]


def test_read_block_decodes_every_data_type_and_applies_gain():
    sun2000 = make_inverter()
    sun2000.read_range = RangeStub(SAMPLE_PAYLOAD)

    values = sun2000.read_block(list(SampleRegister)[:4])

    assert values[SampleRegister.UINT16_WITH_GAIN] == 232.5
    assert values[SampleRegister.INT32_SIGNED] == -1000
    assert values[SampleRegister.WITHOUT_GAIN] == 7
    assert values[SampleRegister.TEXT] == "ABCDE"


def test_read_block_does_not_care_about_the_order_of_the_registers():
    sun2000 = make_inverter()
    sun2000.read_range = RangeStub(SAMPLE_PAYLOAD)
    registers = list(SampleRegister)[:4]

    assert sun2000.read_block(registers) == sun2000.read_block(list(reversed(registers)))


def test_registers_far_apart_end_up_in_separate_requests():
    sun2000 = make_inverter()

    groups = list(sun2000._group_registers([SampleRegister.UINT16_WITH_GAIN, SampleRegister.INT32_SIGNED, SampleRegister.FAR_AWAY]))

    assert [[register.name for register in group] for group in groups] == [["UINT16_WITH_GAIN", "INT32_SIGNED"], ["FAR_AWAY"]]


def chain_of_registers(last_address, step=10):
    """Registers every `step` addresses, so the gaps stay below the gap limit."""
    members = {}
    for address in range(1000, last_address, step):
        members["R%d" % address] = Register(address, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    members["LAST"] = Register(last_address, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None)
    return Enum("Chain%d" % last_address, members)


def spans_of(registers):
    sun2000 = make_inverter()
    return [group[-1].value.address + group[-1].value.quantity - group[0].value.address for group in sun2000._group_registers(registers)]


def test_a_span_of_exactly_the_maximum_stays_in_one_request():
    chain = chain_of_registers(1000 + inverter.MAX_REGISTERS_PER_REQUEST - 1)

    assert spans_of(list(chain)) == [inverter.MAX_REGISTERS_PER_REQUEST]


def test_one_register_beyond_the_maximum_starts_a_new_request():
    chain = list(chain_of_registers(1000 + inverter.MAX_REGISTERS_PER_REQUEST))
    sun2000 = make_inverter()

    groups = list(sun2000._group_registers(chain))

    assert len(groups) == 2
    assert max(spans_of(chain)) <= inverter.MAX_REGISTERS_PER_REQUEST
    assert sum(len(group) for group in groups) == len(chain)


class ClientStub:
    """A Modbus client whose answers the test decides on."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def is_socket_open(self):
        return True

    def connect(self):
        return True

    def read_holding_registers(self, address, quantity, unit=0):
        self.calls.append((address, quantity))
        return self.answer(address, quantity)


class ExceptionAnswer:
    """What pymodbus returns when the inverter rejects a request: not an exception."""

    def __init__(self, exception_code=2):  # 2 = illegal data address
        self.exception_code = exception_code

    def isError(self):
        return True

    def encode(self):
        return bytes([self.exception_code])


def full_answer(address, quantity):
    class Answer:
        def isError(self):
            return False

        def encode(self):
            return bytes([quantity * 2]) + b"\x00\x2a" * quantity
    return Answer()


def test_a_rejected_request_raises_instead_of_decoding_to_zero():
    sun2000 = make_inverter()
    sun2000.inverter = ClientStub(lambda address, quantity: ExceptionAnswer())

    with pytest.raises(ModbusIOException):
        sun2000.read_range(32064, quantity=44)


def test_a_truncated_answer_raises_instead_of_decoding_short():
    sun2000 = make_inverter()
    sun2000.inverter = ClientStub(lambda address, quantity: full_answer(address, 2))

    with pytest.raises(ModbusIOException):
        sun2000.read_range(32064, quantity=44)


def test_a_broken_connection_is_passed_on_instead_of_flooding_the_device():
    """Twelve single reads would only add load to a device that already cannot answer."""
    def break_connection(address, quantity):
        raise ConnectionException("socket closed")

    sun2000 = make_inverter()
    sun2000.inverter = ClientStub(break_connection)

    with pytest.raises(ConnectionException):
        sun2000.read_registers([SampleRegister.UINT16_WITH_GAIN, SampleRegister.INT32_SIGNED])

    assert len(sun2000.inverter.calls) == 1, "only the block read is attempted"


def test_a_model_that_rejects_block_reads_still_gets_all_its_values():
    def reject_ranges(address, quantity):
        return ExceptionAnswer() if quantity > 2 else full_answer(address, quantity)

    sun2000 = make_inverter()
    sun2000.inverter = ClientStub(reject_ranges)
    registers = [SampleRegister.UINT16_WITH_GAIN, SampleRegister.INT32_SIGNED, SampleRegister.WITHOUT_GAIN]

    values = sun2000.read_registers(registers)

    assert set(values) == set(registers)
    assert values[SampleRegister.UINT16_WITH_GAIN] == 4.2
    assert sun2000.inverter.calls[0][1] > 2, "the block read is attempted first"
    assert len(sun2000.inverter.calls) == 1 + len(registers), "then every register on its own"
    assert any("falling back" in message for message in sun2000.logger.messages)


def test_a_rejected_group_is_read_singly_from_then_on_without_repeating_the_warning():
    """Retrying the block every cycle would cost a wasted request and a log line per cycle."""
    def reject_ranges(address, quantity):
        return ExceptionAnswer() if quantity > 2 else full_answer(address, quantity)

    sun2000 = make_inverter()
    sun2000.inverter = ClientStub(reject_ranges)
    registers = [SampleRegister.UINT16_WITH_GAIN, SampleRegister.INT32_SIGNED, SampleRegister.WITHOUT_GAIN]

    sun2000.read_registers(registers)
    calls_after_first_cycle = len(sun2000.inverter.calls)
    values = sun2000.read_registers(registers)

    assert set(values) == set(registers)
    assert len(sun2000.inverter.calls) == calls_after_first_cycle + len(registers), "no block read is tried again"
    assert sum("falling back" in message for message in sun2000.logger.messages) == 1


def test_block_reads_can_be_switched_off():
    sun2000 = make_inverter()
    sun2000.block_read = False
    sun2000.inverter = ClientStub(full_answer)
    registers = [SampleRegister.UINT16_WITH_GAIN, SampleRegister.INT32_SIGNED]

    values = sun2000.read_registers(registers)

    assert set(values) == set(registers)
    assert [quantity for _, quantity in sun2000.inverter.calls] == [1, 2], "one request per register"
    assert sun2000.logger.messages == []


def test_a_busy_device_does_not_get_its_block_reads_switched_off():
    """Device busy (exception code 6) says nothing about the registers, so the block is tried again next cycle."""
    def busy_once(address, quantity):
        if quantity > 2 and not sun2000.inverter.calls[:-1]:
            return ExceptionAnswer(exception_code=6)
        return full_answer(address, quantity)

    sun2000 = make_inverter()
    sun2000.inverter = ClientStub(busy_once)
    registers = [SampleRegister.UINT16_WITH_GAIN, SampleRegister.INT32_SIGNED, SampleRegister.WITHOUT_GAIN]

    sun2000.read_registers(registers)
    calls_after_first_cycle = len(sun2000.inverter.calls)
    sun2000.read_registers(registers)

    assert len(sun2000.inverter.calls) == calls_after_first_cycle + 1, "the second cycle is a single block read again"
