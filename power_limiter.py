#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

"""Decides when the power limit requested by Venus OS is written to the inverter.

The only register that limits a SUN2000-M3 exactly is 40125 (active power in percent),
and the inverter keeps it in non-volatile memory. So the limiter works in steps and
does not write more often than needed:

- The limit is rounded UP to the next step. Rounding down leaves the inverter below
  what ESS asks for; ESS then covers the load from the battery, sees no reason to ask
  for more, and the inverter stays throttled (seen at 0 % for over an hour).
- Two writes are at least `min_interval_seconds` apart. ESS sends a new value every
  5 s, often a little lower each time.
- A lower step is written as soon as that interval allows. The feed-in limit comes first.
- A higher step is written only once Venus has allowed it for the whole hold time, and
  then it is the highest step allowed throughout that time. Venus asks for more only in
  small bits (a few hundred W above the current output), so how far away the real need
  is stays unknown. After a step up the next one comes sooner: the minimum interval after
  the inverter delivers the current step (it ramps up at a few hundred W/s), if Venus's
  latest request then still asks for more. Venus settles in that time, asking for more
  bit by bit, or less after it asked for too much. If it asked for one step more at most
  since the write, and never several steps at once within this ramp, the step is twice
  as big as the one before, up to `max_up_steps`; otherwise it gets what it asks for. Once Venus is content or asks for less, it starts
  again with one step and the full hold time.
- Venus counts as asking for more only if it asks for `up_margin_watt` above the current
  step. At a steady state it sits a few W above; without that margin the limit would
  swing between two steps every half minute.
- While limited, the same step is written again before the inverter's own timeout
  (42019) runs out and it reverts to 100 % by itself.
- Going up counts against an hourly budget of writes. Going down, refreshing and going
  back to full power do not wait for the budget, they only report that it was exceeded.
- If Venus stops sending requests, full power is the wish after `request_timeout`.

No Modbus and no D-Bus in here, the caller hands in the time and carries out the decision.
"""

import math
from collections import namedtuple

Decision = namedtuple("Decision", "level reason over_budget")


class PowerLimiter:
    def __init__(self, max_power, step_percent=1, hold_up_seconds=30, revert_seconds=900,
                 max_writes_per_hour=120, request_timeout=60, retry_seconds=15, min_interval_seconds=15,
                 max_up_steps=4, up_margin_watt=100, request_interval=5):
        if step_percent <= 0 or 100 % step_percent:
            raise ValueError(f"Step size of {step_percent} % does not divide 100 %")
        self.max_power = max_power
        self.step_percent = step_percent
        self.steps = 100 // step_percent
        self.hold_up_seconds = hold_up_seconds
        # Well before the inverter reverts, so a missed cycle or two does not matter.
        self.refresh_seconds = revert_seconds * 2 // 3
        self.max_writes_per_hour = max_writes_per_hour
        self.request_timeout = request_timeout
        self.retry_seconds = retry_seconds
        self.min_interval_seconds = min_interval_seconds
        self.max_up_steps = max_up_steps
        self.up_margin_watt = up_margin_watt
        self.request_interval = request_interval

        self.level = self.steps  # the driver sets 100 % on startup
        self.requested_watt = None
        self.requested_at = None
        self.wishes = []  # (time, step allowed going up) per cycle; the first entry is where the hold time window starts
        self.up_streak = 0  # steps up in a row while Venus kept asking for more
        self.big_ask = False  # Venus asked for several steps more at once within this ramp
        self.last_ask = None  # step allowed going up by the latest request that counts, see _counts()
        self.since_write_max = None  # and the highest since the last write
        self.caught_up_at = None  # when the inverter delivered the step written last
        self.writes = []  # times of the writes within the last hour
        self.last_write = None
        self.retry_at = None
        self.failed_level = None

    def level_for(self, watt):
        """The lowest step that allows at least `watt`."""
        level = math.ceil(watt * self.steps / self.max_power - 1e-9)
        return max(0, min(self.steps, level))

    def percent(self, level):
        return level * self.step_percent

    def watt(self, level):
        return self.max_power * level / self.steps

    def request(self, watt, now):
        self.requested_watt = watt
        self.requested_at = now
        if self._counts(now):
            step = self.level_for(watt - self.up_margin_watt)
            self.last_ask = step
            self.since_write_max = step if self.since_write_max is None else max(self.since_write_max, step)

    def _counts(self, received):
        """Whether a request received at `received` was sent after the last write, and in a
        ramp after the inverter delivered that step.

        The driver timestamps a request when it gets it, and it does not get it while it
        reads the inverter. So a request received shortly after may have been sent before.
        Venus sends one every `request_interval` s, and the one received later than that
        is sure to be new.
        """
        since = self.caught_up_at if self.caught_up_at is not None else self.last_write
        return since is None or received > since + self.request_interval

    def _wish(self, now, margin=0):
        if self.requested_at is None or now - self.requested_at > self.request_timeout:
            return self.steps
        return self.level_for(self.requested_watt - margin)

    def _allowed_since(self, start):
        """The highest step allowed going up throughout the time from `start` to now."""
        in_effect = [step for t, step in self.wishes if t <= start][-1:]
        return min(in_effect + [step for t, step in self.wishes if t > start])

    def _remember(self, wish, now):
        self.wishes.append((now, wish))
        start = now - self.hold_up_seconds
        while len(self.wishes) > 1 and self.wishes[1][0] <= start:
            self.wishes.pop(0)
        self.writes = [t for t in self.writes if t > now - 3600]

    def decide(self, now, output=None):
        """Call once per cycle with the inverter's last output in W. Returns the step to write now, or None."""
        wish = self._wish(now)
        up_wish = self._wish(now, self.up_margin_watt)
        self._remember(up_wish, now)
        if self.up_streak and self.caught_up_at is None and output is not None and output >= self.watt(self.level) * 0.97:
            # Only requests sent from now on count. Venus asks for its measured output plus a
            # bit, so while the inverter ramps up it asks for too little or, when it settles
            # a larger gap, for too much.
            self.caught_up_at = now
            self.last_ask = self.since_write_max = None
        # Silence from Venus is no reason to hurry: full power then waits the whole hold time.
        # Neither is full power asked for, which Venus sends once when it stops limiting.
        if wish == self.steps or self.requested_at is None or now - self.requested_at > self.request_timeout:
            self.up_streak = 0
        # The pause after a failed write must not hold back a limit stricter than the one that failed.
        if self.retry_at is not None and now < self.retry_at and wish >= min(self.failed_level, self.level):
            return None
        if self.last_write is not None and now - self.last_write < self.min_interval_seconds:
            return None

        over_budget = len(self.writes) >= self.max_writes_per_hour
        if wish < self.level:
            return Decision(wish, "down", over_budget)

        if self.up_streak:
            held_long_enough = self.caught_up_at is not None and now - self.caught_up_at >= self.min_interval_seconds
            # Venus settles within that time, asking for more bit by bit or less after asking
            # for too much, so its latest request counts.
            wanted = self.level if self.last_ask is None else self.last_ask
            if held_long_enough and wanted <= self.level:
                self.up_streak = 0  # content after all
            if self.caught_up_at is not None and self.since_write_max is not None and self.since_write_max > self.level + 1:
                self.big_ask = True
            allowed = wanted
            # Once Venus asked for several steps, it tells how much it needs: no jumps on top,
            # also not when it settles to one step more later in the same ramp.
            if self.since_write_max is not None and not self.big_ask:
                allowed = min(max(wanted, self.level + min(2 ** self.up_streak, self.max_up_steps)), self.steps)
        else:
            self.big_ask = False
            held_long_enough = self.wishes[0][0] <= now - self.hold_up_seconds
            wanted = allowed = self._allowed_since(now - self.hold_up_seconds)
            if held_long_enough and wanted > self.level + 1:
                self.big_ask = True
        # Back to full power is never held back by the budget: it ends the limiting and the writes.
        if held_long_enough and wanted > self.level and (not over_budget or wanted == self.steps):
            return Decision(allowed, "up", over_budget)

        if self.level < self.steps and self.last_write is not None and now - self.last_write >= self.refresh_seconds:
            return Decision(self.level, "refresh", over_budget)
        return None

    def adopt(self, level, now):
        """Take over a step found on the inverter at startup and refresh it at the next decision.

        When it was written is unknown, so is the time left until the inverter reverts it.
        """
        self.level = level
        self.last_write = now - self.refresh_seconds

    def written(self, level, now):
        """The inverter confirmed `level`."""
        self.up_streak = self.up_streak + 1 if level > self.level else 0
        self.last_ask = self.since_write_max = self.caught_up_at = None
        self.level = level
        self.last_write = now
        self.writes.append(now)
        self.retry_at = None

    def failed(self, level, now):
        """Writing `level` failed. The step stays as it was, the next attempt waits a little."""
        if level < self.level:
            self.up_streak = 0  # Venus asked for less, that ends a ramp even if the step failed
        self.retry_at = now + self.retry_seconds
        self.failed_level = level
