#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

"""Tests for writing holding registers.

Run with `pytest`. Needs the same pymodbus the driver uses: `pip install pymodbus==2.5.3 pytest`.
"""

from enum import Enum

import pytest
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from pymodbus.register_write_message import WriteMultipleRegistersResponse, WriteSingleRegisterResponse

from sun2000_modbus import datatypes
from sun2000_modbus import inverter
from sun2000_modbus.registers import AccessType, Register

from test_block_read import ExceptionAnswer, make_inverter


class WritableRegister(Enum):
    PERCENT = Register(40125, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RW, None)
    SIGNED = Register(40123, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RW, None)
    SECONDS = Register(42019, 2, datatypes.DataType.UINT32_BE, 1, "s", AccessType.RW, None)
    READ_ONLY = Register(30075, 2, datatypes.DataType.UINT32_BE, 1, "W", AccessType.RO, None)
    TEXT = Register(30000, 15, datatypes.DataType.STRING, None, None, AccessType.RW, None)


class WriteClientStub:
    """A Modbus client that confirms every write unless the test says otherwise."""

    def __init__(self, answer=None):
        self.answer = answer
        self.calls = []
        self.closed = 0

    def is_socket_open(self):
        return True

    def close(self):
        self.closed += 1

    def connect(self):
        return True

    def write_register(self, address, value, unit=0):
        self.calls.append(("single", address, value))
        if self.answer:
            return self.answer(address, value)
        return WriteSingleRegisterResponse(address, value)

    def write_registers(self, address, values, unit=0):
        self.calls.append(("multiple", address, list(values)))
        if self.answer:
            return self.answer(address, values)
        return WriteMultipleRegistersResponse(address, len(values))


def writer(answer=None):
    sun2000 = make_inverter()
    sun2000.inverter = WriteClientStub(answer)
    return sun2000


def test_a_single_register_is_written_with_its_gain_applied():
    sun2000 = writer()

    sun2000.write(WritableRegister.PERCENT, 25)

    assert sun2000.inverter.calls == [("single", 40125, 250)]


def test_a_negative_value_is_sent_as_twos_complement():
    sun2000 = writer()

    sun2000.write(WritableRegister.SIGNED, -0.5)

    assert sun2000.inverter.calls == [("single", 40123, 0x10000 - 500)]


def test_a_32_bit_register_is_written_high_word_first():
    sun2000 = writer()

    sun2000.write(WritableRegister.SECONDS, 70000)

    assert sun2000.inverter.calls == [("multiple", 42019, [1, 70000 - 65536])]


def test_a_read_only_register_is_never_sent():
    sun2000 = writer()

    with pytest.raises(ValueError):
        sun2000.write(WritableRegister.READ_ONLY, 1)

    assert sun2000.inverter.calls == []


def test_a_value_out_of_range_is_never_sent():
    sun2000 = writer()

    with pytest.raises(ValueError):
        sun2000.write(WritableRegister.PERCENT, 6553.6)
    with pytest.raises(ValueError):
        sun2000.write(WritableRegister.PERCENT, -1)

    assert sun2000.inverter.calls == []


def test_a_data_type_without_encoding_is_never_sent():
    sun2000 = writer()

    with pytest.raises(ValueError):
        sun2000.write(WritableRegister.TEXT, "abc")

    assert sun2000.inverter.calls == []


def test_a_refused_write_raises_at_once_without_retrying():
    """Illegal address: the inverter will refuse the same write again, so it is not repeated."""
    sun2000 = writer(lambda address, value: ExceptionAnswer(exception_code=2))
    sun2000.max_retries = 3

    with pytest.raises(inverter.UnsupportedRequest):
        sun2000.write(WritableRegister.PERCENT, 50)

    assert len(sun2000.inverter.calls) == 1


def test_an_echo_with_another_value_is_not_taken_as_confirmation():
    sun2000 = writer(lambda address, value: WriteSingleRegisterResponse(address, 1000))

    with pytest.raises(ModbusIOException):
        sun2000.write(WritableRegister.PERCENT, 50)
    # The real confirmation may still come and would shift the next answer.
    assert sun2000.inverter.closed == 1


def test_an_echo_for_another_address_is_not_taken_as_confirmation():
    sun2000 = writer(lambda address, value: WriteSingleRegisterResponse(40120, value))

    with pytest.raises(ModbusIOException):
        sun2000.write(WritableRegister.PERCENT, 50)


def test_an_answer_meant_for_another_client_is_not_taken_as_confirmation():
    """Seen at the SDongle: a second Modbus client gets its read answers mixed up with ours."""
    sun2000 = writer(lambda address, value: ReadHoldingRegistersResponse([500]))

    with pytest.raises(ModbusIOException):
        sun2000.write(WritableRegister.PERCENT, 50)
    assert sun2000.inverter.closed == 1


def test_a_multiple_write_confirmation_must_match_address_and_count():
    sun2000 = writer(lambda address, values: WriteMultipleRegistersResponse(address, 1))

    with pytest.raises(ModbusIOException):
        sun2000.write(WritableRegister.SECONDS, 900)


def test_a_mixed_up_answer_is_retried_and_the_retry_counts():
    answers = [ReadHoldingRegistersResponse([500]), None]

    def mixed_up_once(address, value):
        answer = answers.pop(0)
        return answer if answer is not None else WriteSingleRegisterResponse(address, value)

    sun2000 = writer(mixed_up_once)
    sun2000.max_retries = 1

    sun2000.write(WritableRegister.PERCENT, 50)

    assert len(sun2000.inverter.calls) == 2


def test_a_broken_connection_is_retried_then_passed_on():
    def break_connection(address, value):
        raise ConnectionException("socket closed")

    sun2000 = writer(break_connection)
    sun2000.max_retries = 2

    with pytest.raises(ConnectionException):
        sun2000.write(WritableRegister.PERCENT, 50)

    assert len(sun2000.inverter.calls) == 3


def test_a_single_attempt_can_be_asked_for():
    def break_connection(address, value):
        raise ConnectionException("socket closed")

    sun2000 = writer(break_connection)
    sun2000.max_retries = 3

    with pytest.raises(ConnectionException):
        sun2000.write(WritableRegister.PERCENT, 50, max_retries=0)

    assert len(sun2000.inverter.calls) == 1


def test_a_confirmation_of_another_transaction_is_retried_on_a_new_connection():
    class Transaction:
        tid = 5

    def answer(address, value):
        response = WriteSingleRegisterResponse(address, value)
        response.transaction_id = 4 if len(sun2000.inverter.calls) == 1 else 5
        return response
    sun2000 = writer(answer)
    sun2000.max_retries = 1
    sun2000.inverter.transaction = Transaction()

    sun2000.write(WritableRegister.PERCENT, 25)

    assert len(sun2000.inverter.calls) == 2
    assert sun2000.inverter.closed == 1
