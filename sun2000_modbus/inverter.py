#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

import time

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException, ConnectionException

from . import datatypes


class RequestRejected(ModbusIOException):
    """The device answered, but refused the request, for instance illegal data address.

    Kept apart from a broken connection on purpose: a refusal says something about the
    request and can be worked around by asking differently, a broken connection cannot.
    """


# A Modbus response can carry at most 125 registers.
MAX_REGISTERS_PER_REQUEST = 125
# Reading a few registers we don't need is much cheaper than sending a second
# request, so we bridge gaps up to this size instead of splitting the block.
MAX_GAP_IN_REGISTERS = 16


class Sun2000:
    def __init__(self, logger, host, port=502, timeout=5, wait=2, modbus_unit=0, max_retries=3, backoff_in_seconds=1, backoff_factor=2.0):  # some models need modbus_unit=1
        self.logger = logger
        self.wait = wait
        self.modbus_unit = modbus_unit
        self.max_retries = max_retries
        self.backoff_in_seconds = backoff_in_seconds
        self.backoff_factor = backoff_factor
        self.inverter = ModbusTcpClient(host, port, timeout=timeout)

    def connect(self):
        if not self.isConnected():
            self.inverter.connect()
            time.sleep(self.wait)
            if self.isConnected():
                self.logger.info('Successfully connected to inverter')
                return True
            else:
                self.logger.error('Connection to inverter failed')
                return False
        else:
            return True

    def disconnect(self):
        """Close the underlying tcp socket"""
        # Some Sun2000 models with the SDongle WLAN-FE require the TCP connection to be closed
        # as soon as possible. Leaving the TCP connection open for an extended time may cause
        # dongle reboots and/or FusionSolar portal updates to be delayed or even paused.
        self.inverter.close()

    def isConnected(self):
        """Check if underlying tcp socket is open"""
        return self.inverter.is_socket_open()

    @property
    def connected(self):
        return self.isConnected()

    @staticmethod
    def _payload(response):
        """Strip the leading byte count from a read response."""
        return response.encode()[1:]

    def _check_response(self, response, start_address, quantity):
        """Reject anything that is not a complete, successful read response.

        A Modbus exception response (illegal address, device busy, ...) is a regular
        object here, not a raised error. Its payload is empty, and an empty byte string
        decodes to 0. Without this check a failed read silently looks like a reading of
        zero, which for a block read would zero every register in the block at once.
        """
        if isinstance(response, ModbusIOException):
            raise response
        if response is None or response.isError():
            raise RequestRejected(f"Inverter refused registers {start_address}..{start_address + quantity - 1}: {response}")
        expected = quantity * 2
        payload = self._payload(response)
        if len(payload) != expected:
            raise RequestRejected(f"Inverter returned {len(payload)} bytes for registers {start_address}..{start_address + quantity - 1}, expected {expected}")

    def read_raw_value(self, register):
        retries = 0
        backoff = self.backoff_in_seconds
        while True:
            if not self.isConnected():
                self.connect()

            if not self.isConnected():
                if retries >= self.max_retries:
                    raise ValueError('Inverter is not connected')
                self.logger.warning(f"Inverter not connected, retrying in {backoff} seconds...")
                time.sleep(backoff)
                retries += 1
                backoff *= self.backoff_factor
                continue

            try:
                register_value = self.inverter.read_holding_registers(register.value.address, register.value.quantity, unit=self.modbus_unit)
                self._check_response(register_value, register.value.address, register.value.quantity)
            except (ConnectionException, ModbusIOException) as e:
                self.logger.error(f"Connection error occurred: {e}")
                if retries >= self.max_retries:
                    raise
                self.logger.warning(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
                retries += 1
                backoff *= self.backoff_factor
                continue

            return datatypes.decode(self._payload(register_value), register.value.data_type)

    def read(self, register):
        raw_value = self.read_raw_value(register)

        if register.value.gain is None:
            return raw_value
        else:
            return raw_value / register.value.gain

    def read_formatted(self, register, use_locale=False):
        return self.format_value(register, self.read(register), use_locale)

    def format_value(self, register, value, use_locale=False):
        """Apply unit or mapping to an already decoded register value."""
        if register.value.unit is not None:
            if use_locale:
                return f'{value:n} {register.value.unit}'
            else:
                return f'{value} {register.value.unit}'
        elif register.value.mapping is not None:
            return register.value.mapping.get(value, f'undefined ({value})')
        else:
            return value

    def read_block(self, registers):
        """Read a group of nearby registers with a single Modbus request.

        The inverter needs roughly the same time to answer a request no matter how
        many registers it covers, so one block read is far quicker than reading every
        register on its own. Returns a dict of register -> value, gain applied.
        """
        registers = list(registers)
        start = min(r.value.address for r in registers)
        end = max(r.value.address + r.value.quantity for r in registers)
        raw = self.read_range(start, quantity=end - start)

        values = {}
        for register in registers:
            offset = (register.value.address - start) * 2
            chunk = raw[offset:offset + register.value.quantity * 2]
            value = datatypes.decode(chunk, register.value.data_type)
            values[register] = value if register.value.gain is None else value / register.value.gain
        return values

    def read_registers(self, registers):
        """Read any set of registers with as few Modbus requests as possible.

        A block covers a few registers the caller did not ask for. Should a model not
        support all of them, the inverter refuses the whole request. In that case this
        falls back to reading the group register by register, so such a model keeps
        working at the old speed instead of losing all of its values at once.

        Only a refusal triggers that fallback. When the connection itself is in trouble,
        replacing one request by twelve would put more load on a device that is already
        struggling, so such an error is passed on and the caller decides.
        """
        values = {}
        for group in self._group_registers(registers):
            try:
                values.update(self.read_block(group))
            except RequestRejected as e:
                first = group[0].value.address
                last = group[-1].value.address + group[-1].value.quantity - 1
                self.logger.warning(f"Block read of registers {first}..{last} failed ({e}), falling back to single reads")
                for register in group:
                    values[register] = self.read(register)
        return values

    @staticmethod
    def _group_registers(registers):
        """Sort registers by address and cut them into blocks a single request can carry."""
        ordered = sorted(set(registers), key=lambda r: r.value.address)
        group = []
        for register in ordered:
            if group:
                span = register.value.address + register.value.quantity - group[0].value.address
                previous = group[-1]
                gap = register.value.address - (previous.value.address + previous.value.quantity)
                if span > MAX_REGISTERS_PER_REQUEST or gap > MAX_GAP_IN_REGISTERS:
                    yield group
                    group = []
            group.append(register)
        if group:
            yield group

    def read_range(self, start_address, quantity=0, end_address=0):
        if quantity == 0 and end_address == 0:
            raise ValueError("Either parameter quantity or end_address is required and must be greater than 0")
        if quantity != 0 and end_address != 0:
            raise ValueError("Only one parameter quantity or end_address should be defined")
        if end_address != 0 and end_address <= start_address:
            raise ValueError("end_address must be greater than start_address")

        if end_address != 0:
            quantity = end_address - start_address + 1

        retries = 0
        backoff = self.backoff_in_seconds
        while True:
            if not self.isConnected():
                self.connect()

            if not self.isConnected():
                if retries >= self.max_retries:
                    raise ValueError('Inverter is not connected')
                self.logger.warning(f"Inverter not connected, retrying in {backoff} seconds...")
                time.sleep(backoff)
                retries += 1
                backoff *= self.backoff_factor
                continue

            try:
                register_range_value = self.inverter.read_holding_registers(start_address, quantity, unit=self.modbus_unit)
                self._check_response(register_range_value, start_address, quantity)
            except (ConnectionException, ModbusIOException) as e:
                self.logger.error(f"Connection error occurred: {e}")
                if retries >= self.max_retries:
                    raise
                self.logger.warning(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
                retries += 1
                backoff *= self.backoff_factor
                continue

            return datatypes.decode(self._payload(register_range_value), datatypes.DataType.MULTIDATA)
