#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

"""Carries out the decisions of the PowerLimiter on the inverter.

Registers involved (tested on SUN2000-30KTL-M3 and -50KTL-M3):
- 40125 active power in percent of the rated power. The inverter keeps it in flash.
- 42014 remote power scheduling. Must be 1, otherwise the inverter refuses 40125.
- 42019 validity of a setpoint in seconds. When it runs out, the inverter goes back to
  100 % by itself, which is the safety net should the driver or the Cerbo fail.
"""

import time

from power_limiter import PowerLimiter

FULL_POWER_PERCENT = 100


class PowerControl:
    REQUIRED_REGISTERS = ("ActivePowerPercentageDerating", "RemotePowerScheduling", "ScheduleInstructionValidDuration", "MaximumActivePower")

    def __init__(self, sun2000, registers, logger, revert_seconds=900, sleep=time.sleep, **limiter_settings):
        self.sun2000 = sun2000
        self.sleep = sleep
        self.registers = registers
        self.logger = logger
        self.revert_seconds = revert_seconds
        self.limiter_settings = limiter_settings
        self.limiter = None

    def prepare(self, now):
        """Get the inverter ready to be limited. Returns False if it cannot be.

        Settings are written only if they differ, so a restart does not wear the flash.
        A step left from before a restart is kept, so the inverter does not run at full
        power until ESS is back. Anything else that is not 100 % is reset to 100 %.
        """
        missing = [name for name in self.REQUIRED_REGISTERS if name not in self.registers.__members__]
        if missing:
            self.logger.error(f"Power limit not possible with this register map, missing: {', '.join(missing)}")
            return False
        r = self.registers
        try:
            max_power = self.sun2000.read(r.MaximumActivePower)
            if not max_power > 0:
                raise ValueError(f"rated power {max_power} W")
            if self.sun2000.read(r.RemotePowerScheduling) != 1:
                self.logger.info("Enabling remote power scheduling (42014 = 1), needed for the power limit")
                self.sun2000.write(r.RemotePowerScheduling, 1)
            if self.sun2000.read(r.ScheduleInstructionValidDuration) != self.revert_seconds:
                self.logger.info(f"Setting the inverter's fallback to full power to {self.revert_seconds} s (42019)")
                self.sun2000.write(r.ScheduleInstructionValidDuration, self.revert_seconds)
                # A multiple write is confirmed without the value, so read it back. A SUN2000-30KTL-M3
                # still returned the old value right after the write, so give it a few seconds.
                for _ in range(3):
                    self.sleep(1)
                    if self.sun2000.read(r.ScheduleInstructionValidDuration) == self.revert_seconds:
                        break
                else:
                    raise ValueError("42019 did not take the new value")
            self.limiter = PowerLimiter(max_power=max_power, revert_seconds=self.revert_seconds, **self.limiter_settings)
            percent = self.sun2000.read(r.ActivePowerPercentageDerating)
            level = percent / self.limiter.step_percent
            if percent != FULL_POWER_PERCENT and 0 <= percent < FULL_POWER_PERCENT and abs(level - round(level)) < 1e-6:
                self.logger.info(f"Inverter is limited to {percent:g} % from before, keeping it until ESS asks for more")
                self.limiter.adopt(round(level), now)
            elif percent != FULL_POWER_PERCENT:
                self.logger.info(f"Inverter is at {percent:g} %, not one of our steps, setting 100 % (40125)")
                self.sun2000.write(r.ActivePowerPercentageDerating, FULL_POWER_PERCENT)
        except Exception as e:
            self.logger.error(f"Power limit disabled, preparing the inverter failed: {e}")
            self.limiter = None
            # A limit left from before would otherwise stay, possibly without a working fallback.
            try:
                if self.sun2000.read(r.ActivePowerPercentageDerating) != FULL_POWER_PERCENT:
                    self.sun2000.write(r.ActivePowerPercentageDerating, FULL_POWER_PERCENT)
                    self.logger.info("Power limit lifted")
            except Exception as e:
                self.logger.error(f"Lifting the power limit failed: {e}")
            return False
        self.logger.info(f"Power limit ready: {self.limiter.steps} steps of {self.limiter.step_percent} % of {max_power:.0f} W")
        return True

    def step(self, now, output=None):
        """Call once per cycle before reading, with the output read last. Returns the step written, or None."""
        decision = self.limiter.decide(now, output)
        if decision is None:
            return None
        percent = self.limiter.percent(decision.level)
        try:
            # A single attempt: retries would block the main loop, and with it any new request
            # from ESS, for up to a minute. The limiter tries again after a short pause.
            self.sun2000.write(self.registers.ActivePowerPercentageDerating, percent, max_retries=0)
        except Exception as e:
            self.limiter.failed(decision.level, now)
            self.logger.error(f"Writing power limit {percent} % failed: {e}")
            return None
        self.limiter.written(decision.level, now)
        message = f"Power limit {percent} % ({self.limiter.watt(decision.level):.0f} W), {decision.reason}"
        if decision.over_budget:
            self.logger.warning(message + f", more than {self.limiter.max_writes_per_hour} writes within the last hour")
        elif decision.reason == "refresh":
            self.logger.debug(message)
        else:
            self.logger.info(message)
        return decision.level

    def release(self):
        """On shutdown: back to full power, but only if limited, to spare the flash.

        Asks the inverter rather than trusting the last confirmed step: a write whose
        confirmation got lost may have taken effect all the same.
        """
        if self.limiter is None:
            return
        try:
            if self.sun2000.read(self.registers.ActivePowerPercentageDerating) == FULL_POWER_PERCENT:
                return
            self.sun2000.write(self.registers.ActivePowerPercentageDerating, FULL_POWER_PERCENT)
            self.logger.info("Power limit lifted on shutdown")
        except Exception as e:
            self.logger.error(f"Lifting the power limit on shutdown failed, the inverter reverts within {self.revert_seconds} s: {e}")
