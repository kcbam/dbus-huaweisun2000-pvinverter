#!/usr/bin/env python3
# Please adhere to flake8 --ignore E501,E402

"""Tests for the decisions of the power limiter. No Modbus, no D-Bus, time is handed in."""

import pytest

from power_limiter import PowerLimiter

PMAX = 55000  # SUN2000-50KTL-M3
STEP = PMAX / 20


def limiter(**kwargs):
    """Coarse settings, so the mechanics show in a few steps. The defaults are tested below."""
    settings = dict(step_percent=5, hold_up_seconds=300, max_writes_per_hour=12, min_interval_seconds=0)
    settings.update(kwargs)
    return PowerLimiter(max_power=PMAX, **settings)


def run(pl, start, end, watt=None, every=1):
    """Call decide() once per cycle like the driver does, execute every decision, return them."""
    decisions = []
    for now in range(start, end, every):
        if watt is not None:
            pl.request(watt, now)
        decision = pl.decide(now)
        if decision:
            pl.written(decision.level, now)
            decisions.append((now, decision))
    return decisions


def test_a_limit_is_rounded_up_to_the_next_step():
    pl = limiter()

    assert pl.level_for(STEP * 3) == 3
    assert pl.level_for(STEP * 3 + 1) == 4
    assert pl.level_for(STEP * 3 - 1) == 3
    assert pl.level_for(1) == 1
    assert pl.level_for(0) == 0
    assert pl.level_for(-500) == 0
    assert pl.level_for(PMAX * 2) == 20


def test_a_step_is_written_as_percent_of_rated_power():
    pl = limiter()

    assert pl.percent(3) == 15
    assert pl.watt(3) == 8250


def test_a_step_size_that_does_not_divide_100_is_refused():
    with pytest.raises(ValueError):
        limiter(step_percent=7)


def test_nothing_is_written_without_a_limit():
    pl = limiter()

    assert run(pl, 0, 7200) == []
    assert run(pl, 7200, 14400, watt=PMAX) == []


def test_a_lower_limit_is_written_at_once():
    pl = limiter()

    decisions = run(pl, 0, 2, watt=STEP * 4.5)

    assert [(now, d.level, d.reason) for now, d in decisions] == [(0, 5, "down")]


def test_a_higher_limit_waits_for_the_hold_time():
    pl = limiter()
    run(pl, 0, 1, watt=STEP * 4)

    decisions = run(pl, 1, 400, watt=STEP * 10)

    assert [(now, d.level, d.reason) for now, d in decisions] == [(301, 10, "up")]


def test_going_up_uses_the_highest_step_allowed_throughout_the_hold_time():
    pl = limiter()
    run(pl, 0, 1, watt=STEP * 4)
    run(pl, 1, 100, watt=STEP * 12)
    run(pl, 100, 200, watt=STEP * 8)  # a dip, but still above the current step

    decisions = run(pl, 200, 400, watt=STEP * 12)

    assert [(now, d.level) for now, d in decisions][0] == (301, 8)


def test_a_dip_below_the_current_step_is_followed_at_once_and_restarts_the_hold_time():
    pl = limiter()
    run(pl, 0, 1, watt=STEP * 10)
    run(pl, 1, 200, watt=STEP * 20)

    decisions = run(pl, 200, 201, watt=STEP * 6) + run(pl, 201, 600, watt=STEP * 20)

    assert [(now, d.level, d.reason) for now, d in decisions] == [(200, 6, "down"), (501, 20, "up")]


def test_back_at_full_power_nothing_is_refreshed():
    pl = limiter()
    run(pl, 0, 1, watt=STEP * 10)

    decisions = run(pl, 1, 7200, watt=PMAX)

    assert [(now, d.level) for now, d in decisions] == [(301, 20)]


def test_a_limit_is_refreshed_before_the_inverter_reverts_it():
    pl = limiter(revert_seconds=900)

    decisions = run(pl, 0, 1900, watt=STEP * 10)

    assert [(now, d.reason) for now, d in decisions] == [(0, "down"), (600, "refresh"), (1200, "refresh"), (1800, "refresh")]
    gaps = [b - a for (a, _), (b, _) in zip(decisions, decisions[1:])]
    assert max(gaps) < 900


def test_without_new_requests_the_limit_is_lifted_after_timeout_and_hold_time():
    """Venus writes regularly. After 60 s of silence full power is the wish, but going up still waits 5 min."""
    pl = limiter()
    run(pl, 0, 1, watt=STEP * 10)

    decisions = run(pl, 1, 600)

    assert [(now, d.level, d.reason) for now, d in decisions] == [(361, 20, "up")]


def test_going_up_stops_when_the_hourly_budget_is_used_up():
    pl = limiter(max_writes_per_hour=3, revert_seconds=7200)  # no refresh within the hour
    # three writes: down to 10, up to 15, down to 5
    run(pl, 0, 1, watt=STEP * 10)
    run(pl, 1, 302, watt=STEP * 15)
    run(pl, 302, 303, watt=STEP * 5)

    blocked = run(pl, 303, 3600, watt=STEP * 15)
    released = run(pl, 3600, 3700, watt=STEP * 15)

    assert blocked == []
    assert [(now, d.level, d.reason) for now, d in released] == [(3600, 15, "up")]


def test_going_down_ignores_the_budget_and_says_so():
    """The feed-in limit comes first. Protecting the inverter's memory comes second."""
    pl = limiter(max_writes_per_hour=1)
    run(pl, 0, 1, watt=STEP * 10)

    decisions = run(pl, 1, 3, watt=STEP * 5)

    assert [(d.level, d.reason, d.over_budget) for _, d in decisions] == [(5, "down", True)]


def test_a_refresh_ignores_the_budget_so_the_limit_does_not_lapse():
    pl = limiter(max_writes_per_hour=1)

    decisions = run(pl, 0, 700, watt=STEP * 10)

    assert [(now, d.reason, d.over_budget) for now, d in decisions] == [(0, "down", False), (600, "refresh", True)]


def test_a_failed_write_keeps_the_old_step_and_is_retried_after_a_pause():
    pl = limiter(retry_seconds=10)
    pl.request(STEP * 10, 0)
    pl.decide(0)
    pl.failed(10, 0)

    assert pl.level == 20
    assert pl.decide(5) is None
    assert pl.decide(10).level == 10


def test_a_stricter_limit_is_written_during_the_pause_after_a_failed_write():
    pl = limiter(retry_seconds=10)
    pl.request(STEP * 10, 0)
    pl.failed(pl.decide(0).level, 0)

    pl.request(STEP * 4, 1)

    assert pl.decide(1).level == 4


def test_the_defaults_follow_a_limit_below_one_coarse_step():
    """HW1, 27.09.2026: ESS asked for about 870 W. Rounded down to 5 % steps that was 0 %;
    the battery covered the load, ESS never asked for more and the inverter stayed off."""
    pl = PowerLimiter(max_power=PMAX)

    pl.request(870, 0)

    assert pl.decide(0).level == 2  # 1 % steps of 550 W, rounded up: 1100 W
    assert pl.watt(2) >= 870


def test_writes_keep_a_minimum_interval_also_going_down():
    """ESS sends a new value every 5 s, often a little lower each time."""
    pl = PowerLimiter(max_power=PMAX, min_interval_seconds=15)
    decisions = []
    for now in range(0, 40, 5):
        pl.request(20000 - 500 * now, now)
        decision = pl.decide(now)
        if decision:
            pl.written(decision.level, now)
            decisions.append((now, decision.level))

    assert [now for now, _ in decisions] == [0, 15, 30]
    assert decisions[-1][1] == pl.level_for(20000 - 500 * 30)


def test_full_power_after_a_timeout_ignores_the_budget():
    pl = limiter(max_writes_per_hour=1, hold_up_seconds=30)
    run(pl, 0, 1, watt=STEP * 10)

    decisions = run(pl, 1, 200)  # Venus silent from now on

    assert [(now, d.level, d.reason, d.over_budget) for now, d in decisions] == [(91, 20, "up", True)]


def test_by_default_a_failed_write_is_not_retried_sooner_than_the_minimum_interval():
    pl = PowerLimiter(max_power=PMAX)
    pl.request(10000, 0)
    pl.failed(pl.decide(0).level, 0)

    assert all(pl.decide(now) is None for now in range(1, 15))
    assert pl.decide(15) is not None


def ess_like(pl, need, start, end):
    """ESS as seen on HW1, 28.09.2026, with the battery covering the gap: while it wants more
    it asks for about 270 W above the inverter's output, never for the real need. The
    inverter ramps at 275 W/s. ESS sends every 5 s, the driver decides every second.
    Returns the steps written, with time."""
    decisions = []
    sent = None
    output = pl.watt(pl.level)
    for now in range(start, end):
        target = pl.watt(pl.level)
        output = min(output + 275, target) if output < target else target
        # Sent out of step with the driver and delivered up to 4 s later, once the driver has
        # read the inverter: it may still refer to the step before a write (HW1, 28.09.2026).
        if now % 5 == 3:
            sent = (now, min(output + 270, need))
        decision = pl.decide(now, output)
        if decision:
            pl.written(decision.level, now)
            decisions.append((now, decision.level))
        if sent is not None and now == sent[0] + 4:
            pl.request(sent[1], now + 0.5)
    return decisions


def test_going_up_gets_faster_while_ess_keeps_asking_for_more():
    """An 11 kW car starts while limited to 1100 W: ESS asks for a little more each time."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    need = 12100

    decisions = ess_like(pl, need, 5, 300)

    reached = next(now for now, level in decisions if pl.watt(level) >= need)
    assert reached - decisions[0][0] <= 6 * 22  # six more steps: the inverter ramps up, then 5 s plus the minimum interval
    ups = [b - a for (_, a), (_, b) in zip([(0, 2)] + decisions, decisions) if b > a]
    assert ups[:4] == [1, 2, 4, 4]
    assert max(level for _, level in decisions) - pl.level_for(need) <= pl.max_up_steps
    assert decisions[-1][1] == pl.level_for(need)  # an overshoot is followed down


def test_ess_just_above_the_current_step_does_not_move_it():
    """At a steady state ESS sits a few W above the step (1111 to 1124 W at 1100 W on HW1)."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)

    assert run(pl, 1, 600, watt=1124) == []
    assert [d.level for _, d in run(pl, 600, 700, watt=1100 + 270) if d.reason == "up"][:1] == [3]


def test_after_going_down_going_up_starts_again_with_one_step_and_the_hold_time():
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    ess_like(pl, 5000, 5, 90)
    down = run(pl, 90, 120, watt=1100)
    assert [d.reason for _, d in down] == ["down"]

    decisions = ess_like(pl, 20000, 120, 200)

    assert decisions[0][1] == 3
    assert decisions[0][0] - down[0][0] >= pl.hold_up_seconds


def test_a_jump_capped_at_full_power_still_counts_against_the_budget():
    """Only a real wish for full power may ignore the budget, not a jump that ends there."""
    pl = PowerLimiter(max_power=PMAX, max_writes_per_hour=2)
    pl.request(PMAX * 0.97, 0)
    pl.written(pl.decide(0).level, 0)  # 97 %
    ess_like(pl, PMAX * 0.99, 5, 50)  # up to 98 %: budget used up, streak going

    assert pl.level == 98
    assert ess_like(pl, PMAX * 0.99, 50, 600) == []


def test_silence_from_ess_waits_the_whole_hold_time_even_during_a_ramp():
    pl = PowerLimiter(max_power=PMAX, max_writes_per_hour=2)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    ess_like(pl, 20000, 5, 65)  # up at 35, then the budget blocks, streak going
    last_request = pl.requested_at

    decisions = run(pl, 65, 300)  # ESS silent

    assert [(now, d.level) for now, d in decisions] == [(int(last_request + 60) + 1 + 30, pl.steps)]


def test_after_a_failed_step_up_only_going_down_is_written_during_the_pause():
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    ess_like(pl, 20000, 5, 45)  # up to 3 at 43, streak going
    assert pl.decide(45, output=pl.watt(pl.level)) is None  # the inverter delivers it
    pl.request(pl.watt(pl.level) + 270, 53)
    pl.request(pl.watt(pl.level) + 270, 58)
    pl.failed(pl.decide(60, output=pl.watt(pl.level)).level, 60)  # the jump to 5 failed

    pl.request(pl.watt(pl.level) + 200, 62)
    assert pl.decide(62) is None
    pl.request(500, 65)
    assert pl.decide(65).level == 1


def test_a_quicker_step_up_waits_until_the_inverter_delivers_the_current_one():
    """HW1, 28.09.2026: the inverter ramps up at about 275 W/s. ESS kept asking for more
    meanwhile and the driver went on to 25 % while the need was 19 %."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    ess_like(pl, 20000, 5, 44)  # up to 3 at 43, streak going
    for now in range(44, 65):
        if now % 5 == 0:
            pl.request(pl.watt(pl.level) + 2000, now)  # asking for too much while the inverter ramps up
        assert pl.decide(now, output=pl.watt(pl.level) * 0.9) is None

    decisions = []
    for now in range(65, 90):  # delivers the step from 65 on, ESS settles to a little more
        if now % 5 == 0:
            pl.request(pl.watt(pl.level) + 270, now)
        decision = pl.decide(now, output=pl.watt(pl.level))
        if decision:
            pl.written(decision.level, now)
            decisions.append((now, decision.level))

    assert decisions[0] == (80, 5)  # 15 s after catching up, twice the step before, not the 2000 W


def test_an_unknown_output_does_not_count_as_caught_up():
    """A failed read leaves no fresh output after a write; the old one would look delivered."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    ess_like(pl, 20000, 5, 44)  # up to 3 at 43, streak going
    for now in range(44, 65):
        if now % 5 == 0:
            pl.request(pl.watt(pl.level) + 270, now)
        assert pl.decide(now, output=None) is None

    decisions = []
    for now in range(65, 90):
        if now % 5 == 0:
            pl.request(pl.watt(pl.level) + 270, now)
        decision = pl.decide(now, output=pl.watt(pl.level))
        if decision:
            pl.written(decision.level, now)
            decisions.append((now, decision.level))

    assert decisions[0][0] == 80  # 15 s after the first known output, not before


def test_when_ess_asks_for_several_steps_more_it_gets_the_least_of_it_without_a_jump():
    """HW1, 28.09.2026, feed-in limit raised by 9.5 kW with a full battery: ESS asked for
    several steps more and settled over about 15 s once the inverter got there."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    assert [(now, d.level) for now, d in run(pl, 1, 32, watt=7000)] == [(31, 13)]  # streak going
    assert pl.decide(32, output=pl.watt(pl.level)) is None  # the inverter delivers it

    for now, watt in ((37, 13000), (42, 12000), (47, 11000)):
        pl.request(watt, now)
    decision = pl.decide(47, output=pl.watt(pl.level))

    assert decision.level == pl.level_for(11000 - 100)  # 20 %
    pl.written(decision.level, 47)

    assert pl.decide(48, output=pl.watt(pl.level)) is None
    for now in (53, 58, 63):
        pl.request(pl.watt(22) + 50, now)  # two steps more
    decision = pl.decide(63, output=pl.watt(pl.level))

    assert decision.level == 22  # not 20 + 4


def test_full_power_asked_for_during_a_ramp_follows_after_the_hold_time():
    """HW1, 28.09.2026: ESS sends the rated power once when it stops limiting. Within the
    ramp the least request since the last step hid it, and full power waited for the timeout."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    ess_like(pl, 20000, 5, 60)  # ramp going
    pl.request(PMAX, 60)

    decisions = run(pl, 60, 200)

    now, level = [(now, d.level) for now, d in decisions if d.reason == "up"][-1]
    assert level == pl.steps
    assert now <= 60 + pl.hold_up_seconds + pl.min_interval_seconds  # not after the 60 s timeout


def test_ess_asking_for_more_bit_by_bit_after_the_inverter_caught_up_keeps_the_ramp_going():
    """HW1, 28.09.2026, battery covering the gap: after the inverter got to 2750 W, ESS asked
    for 2783, 2919, 2979 W. The first one alone looked content and ended the ramp."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    assert [(now, d.level) for now, d in run(pl, 1, 32, watt=1100 + 270)] == [(31, 3)]
    assert pl.decide(32, output=pl.watt(3)) is None  # the inverter delivers it

    for now, above in ((38, 34), (43, 170), (47, 230)):
        pl.request(pl.watt(3) + above, now)
    decision = pl.decide(47, output=pl.watt(3))

    assert decision.level == 5  # one step more asked for, twice the step before


def test_asking_for_less_ends_a_ramp_even_if_the_lower_step_fails():
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    assert [(now, d.level) for now, d in run(pl, 1, 32, watt=1100 + 270)] == [(31, 3)]  # streak going
    pl.request(500, 46)
    pl.failed(pl.decide(46).level, 46)  # going down to 1 failed

    decisions = run(pl, 47, 120, watt=pl.watt(5) + 270)  # and then for more again

    assert decisions[0][0] - 46 >= pl.hold_up_seconds


def test_after_asking_for_several_steps_one_step_more_later_in_the_ramp_gets_no_jump():
    """HW1, 28.09.2026, feed-in limit raised by 9.5 kW: ESS asked for 12 % at once, settled to
    one step more at 17 % and the jump on top went to 21 % while 19 % was needed."""
    pl = PowerLimiter(max_power=PMAX)
    pl.request(1100, 0)
    pl.written(pl.decide(0).level, 0)
    assert [(now, d.level) for now, d in run(pl, 1, 32, watt=7000)] == [(31, 13)]  # several steps at once
    assert pl.decide(32, output=pl.watt(13)) is None  # the inverter delivers it

    for now in (38, 43, 47):
        pl.request(pl.watt(13) + 270, now)  # settled to one step more
    decision = pl.decide(47, output=pl.watt(13))

    assert decision.level == 14
