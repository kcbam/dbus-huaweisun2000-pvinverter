#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

"""Tests for what the power control writes to the inverter at start, per cycle and on shutdown."""

from pymodbus.exceptions import ConnectionException

from power_control import PowerControl
from power_limiter import PowerLimiter
from sun2000_modbus import inverter
from sun2000_modbus.inverter_registers import InverterRegisterV2, InverterRegisterV3

from test_block_read import LoggerSpy

R = InverterRegisterV3


class InverterFake:
    """Holds register values like the inverter and records every write."""

    def __init__(self, **values):
        self.values = {R.RemotePowerScheduling: 1, R.ScheduleInstructionValidDuration: 900,
                       R.ActivePowerPercentageDerating: 100, R.MaximumActivePower: 55000}
        self.values.update({R[name]: value for name, value in values.items()})
        self.writes = []
        self.refuse = None

    def read(self, register):
        return self.values[register]

    def write(self, register, value, max_retries=None):
        self.max_retries = max_retries
        if self.refuse:
            raise self.refuse
        self.writes.append((register.value.address, value))
        self.values[register] = value


def control(fake, registers=R):
    return PowerControl(fake, registers, LoggerSpy(), revert_seconds=900, sleep=lambda seconds: None, step_percent=5, min_interval_seconds=0)


def test_a_prepared_inverter_is_left_alone():
    fake = InverterFake()
    pc = control(fake)

    assert pc.prepare(0)
    assert fake.writes == []
    assert pc.limiter.max_power == 55000


def test_prepare_enables_scheduling_and_sets_the_fallback():
    fake = InverterFake(RemotePowerScheduling=0, ScheduleInstructionValidDuration=0)
    pc = control(fake)

    assert pc.prepare(0)
    assert fake.writes == [(42014, 1), (42019, 900)]


def test_a_fallback_that_shows_up_late_is_waited_for():
    """ZDD12, 28.09.2026: the SUN2000-30KTL-M3 still returned the old 42019 right after the write."""
    fake = InverterFake(ScheduleInstructionValidDuration=0)
    reads = []
    real_read = fake.read

    def read(register):
        reads.append(register)
        if register == R.ScheduleInstructionValidDuration and reads.count(register) <= 2:
            return 0  # the check before the write, then the first read after it
        return real_read(register)
    fake.read = read
    pc = control(fake)

    assert pc.prepare(0)
    assert pc.limiter is not None


def test_a_step_left_from_before_a_restart_is_kept_and_refreshed_at_once():
    """Writing 100 % first would let the inverter run at full power until ESS is back."""
    fake = InverterFake(ActivePowerPercentageDerating=45)
    pc = control(fake)

    assert pc.prepare(0)
    assert fake.writes == []
    assert pc.limiter.level == 9
    pc.limiter.request(55000, 1)
    assert pc.step(1) == 9
    assert fake.writes == [(40125, 45)]


def test_a_value_that_is_not_one_of_our_steps_is_reset_to_full_power():
    fake = InverterFake(ActivePowerPercentageDerating=99.9)
    pc = control(fake)

    assert pc.prepare(0)
    assert fake.writes == [(40125, 100)]
    assert pc.limiter.level == 20


def test_a_fallback_that_does_not_stick_disables_the_power_limit():
    fake = InverterFake(ScheduleInstructionValidDuration=0)
    fake.write = lambda register, value: None  # confirmed, but the value stays
    pc = control(fake)

    assert not pc.prepare(0)
    assert pc.limiter is None


def test_a_refusing_inverter_disables_the_power_limit():
    fake = InverterFake(RemotePowerScheduling=0)
    fake.refuse = inverter.UnsupportedRequest("illegal data address")
    pc = control(fake)

    assert not pc.prepare(0)
    assert any("disabled" in message for message in pc.logger.messages)


def test_a_register_map_without_the_registers_disables_the_power_limit():
    fake = InverterFake()
    pc = control(fake, registers=InverterRegisterV2)

    assert not pc.prepare(0)
    assert fake.writes == []


def test_a_decision_is_written_as_percent():
    fake = InverterFake()
    pc = control(fake)
    pc.prepare(0)
    pc.limiter.request(55000 * 0.47, 0)

    assert pc.step(0) == 10
    assert fake.writes == [(40125, 50)]
    assert fake.max_retries == 0, "retries would block the main loop"
    assert pc.step(1) is None


def test_a_failed_write_keeps_the_step_and_is_tried_again_later():
    fake = InverterFake()
    pc = control(fake)
    pc.prepare(0)
    pc.limiter.request(10000, 0)
    fake.refuse = ConnectionException("socket closed")

    assert pc.step(0) is None
    assert pc.limiter.level == 20
    fake.refuse = None
    assert pc.step(1) is None
    assert pc.step(15) == 4  # 10000 W rounded up to 5 % steps: 11000 W


def test_shutdown_lifts_a_limit():
    fake = InverterFake()
    pc = control(fake)
    pc.prepare(0)
    pc.limiter.request(10000, 0)
    pc.step(0)

    pc.release()

    assert fake.writes[-1] == (40125, 100)


def test_shutdown_without_a_limit_writes_nothing():
    fake = InverterFake()
    pc = control(fake)
    pc.prepare(0)

    pc.release()

    assert fake.writes == []


def test_shutdown_lifts_a_limit_whose_confirmation_got_lost():
    fake = InverterFake()
    pc = control(fake)
    pc.limiter = PowerLimiter(max_power=55000)  # the driver never saw the limit confirmed
    fake.values[R.ActivePowerPercentageDerating] = 45

    pc.release()

    assert fake.writes == [(40125, 100)]


def test_an_invalid_step_size_disables_the_power_limit_instead_of_crashing():
    fake = InverterFake()
    pc = PowerControl(fake, R, LoggerSpy(), revert_seconds=900, step_percent=7)

    assert not pc.prepare(0)


def test_a_failed_prepare_lifts_a_limit_left_from_before():
    """42014 is enabled, then 42019 fails: the stored limit must not stay without a fallback."""
    fake = InverterFake(RemotePowerScheduling=0, ScheduleInstructionValidDuration=0, ActivePowerPercentageDerating=45)
    write = fake.write

    def refuse_the_fallback(register, value, max_retries=None):
        if register == R.ScheduleInstructionValidDuration:
            raise inverter.RequestRejected("no answer")
        write(register, value, max_retries)
    fake.write = refuse_the_fallback
    pc = control(fake)

    assert not pc.prepare(0)
    assert fake.values[R.ActivePowerPercentageDerating] == 100


def test_an_unknown_rated_power_disables_the_power_limit_before_any_write():
    fake = InverterFake(RemotePowerScheduling=0, MaximumActivePower=0)
    pc = control(fake)

    assert not pc.prepare(0)
    assert fake.writes == []
