from __future__ import annotations

from dataclasses import replace

import pytest

from albatross.domain.config import (
    DEFAULT_FLIGHT_CONFIG,
    SPEED_CYCLE,
    SPEED_FACTORS,
    SpeedPreset,
    next_speed,
)
from albatross.domain.flight import FlightModel
from albatross.domain.session import GamePhase, GameSession


def test_speed_cycle_wraps_around() -> None:
    assert next_speed(SpeedPreset.CALM) is SpeedPreset.NORMAL
    assert next_speed(SpeedPreset.NORMAL) is SpeedPreset.SWIFT
    assert next_speed(SpeedPreset.SWIFT) is SpeedPreset.CALM
    assert set(SPEED_FACTORS) == set(SPEED_CYCLE)


def test_speed_presets_scale_every_motion_rate() -> None:
    base = FlightModel(DEFAULT_FLIGHT_CONFIG).advance(
        FlightModel(DEFAULT_FLIGHT_CONFIG).initial_state(),
        1.0,
    )

    for preset, factor in SPEED_FACTORS.items():
        model = FlightModel(replace(DEFAULT_FLIGHT_CONFIG, speed=preset))
        state = model.advance(model.initial_state(), 1.0)
        assert state.x_m == pytest.approx(base.x_m * factor), preset
        assert state.vertical_speed_mps == pytest.approx(base.vertical_speed_mps * factor), preset


def test_flap_strength_follows_the_speed_preset() -> None:
    model = FlightModel(replace(DEFAULT_FLIGHT_CONFIG, speed=SpeedPreset.SWIFT))
    state, accepted = model.flap(model.initial_state())

    assert accepted
    assert state.vertical_speed_mps == pytest.approx(
        -DEFAULT_FLIGHT_CONFIG.flap_up_speed_mps * SPEED_FACTORS[SpeedPreset.SWIFT]
    )


def test_set_speed_is_allowed_between_runs_only() -> None:
    session = GameSession(DEFAULT_FLIGHT_CONFIG)
    assert session.config.speed is SpeedPreset.NORMAL

    assert session.set_speed(SpeedPreset.SWIFT) is True
    assert session.state.speed is SpeedPreset.SWIFT
    assert session.config.speed is SpeedPreset.SWIFT
    assert session.set_speed(SpeedPreset.SWIFT) is False  # same preset: no-op

    session.start()
    assert session.state.phase is GamePhase.PLAYING
    assert session.set_speed(SpeedPreset.CALM) is False  # mid-run: rejected
    assert session.state.speed is SpeedPreset.SWIFT


def test_speed_change_on_game_over_applies_to_the_next_run() -> None:
    session = GameSession(replace(DEFAULT_FLIGHT_CONFIG, start_altitude_m=0.01, step_s=0.1))
    session.start()
    assert session.advance(0.1)
    assert session.state.phase is GamePhase.GAME_OVER

    assert session.set_speed(SpeedPreset.CALM) is True
    assert session.restart() is True

    before = session.state.flight.x_m
    session.advance(0.1)
    normal_step = DEFAULT_FLIGHT_CONFIG.horizontal_speed_mps * 0.1
    assert session.state.flight.x_m - before == pytest.approx(
        normal_step * SPEED_FACTORS[SpeedPreset.CALM]
    )


def test_speed_change_in_pause_is_rejected() -> None:
    session = GameSession(DEFAULT_FLIGHT_CONFIG)
    session.start()
    session.toggle_pause()

    assert session.set_speed(SpeedPreset.SWIFT) is False
    assert session.state.speed is SpeedPreset.NORMAL
