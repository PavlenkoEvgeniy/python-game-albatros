from __future__ import annotations

import pytest

from albatross.application.timing import FixedStepClock

STEP = 1.0 / 120.0


def test_same_elapsed_time_gives_the_same_step_count() -> None:
    slow = FixedStepClock(step_s=STEP, max_frame_s=0.25)
    fast = FixedStepClock(step_s=STEP, max_frame_s=0.25)

    slow_steps = slow.feed(1.0 / 30.0)
    fast_steps = fast.feed(1.0 / 60.0) + fast.feed(1.0 / 60.0)

    assert slow_steps == fast_steps == 4


def test_leftover_time_is_carried_over() -> None:
    clock = FixedStepClock(step_s=1.0, max_frame_s=10.0)

    assert clock.feed(0.6) == 0
    assert clock.feed(0.6) == 1


def test_long_frame_is_clamped() -> None:
    clock = FixedStepClock(step_s=0.01, max_frame_s=0.25)

    assert clock.feed(10.0) == 25
    assert clock.feed(0.0) == 0


def test_negative_frame_time_is_ignored() -> None:
    clock = FixedStepClock(step_s=0.1, max_frame_s=1.0)

    assert clock.feed(-5.0) == 0
    assert clock.feed(0.1) == 1


@pytest.mark.parametrize("fps", [30, 60, 144])
def test_one_second_is_one_second_at_any_frame_rate(fps: int) -> None:
    clock = FixedStepClock(step_s=STEP, max_frame_s=0.25)
    steps = sum(clock.feed(1.0 / fps) for _ in range(fps))

    assert abs(steps - 120) <= 1
