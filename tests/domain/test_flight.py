from __future__ import annotations

from dataclasses import replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from albatross.domain.config import DEFAULT_FLIGHT_CONFIG
from albatross.domain.flight import FlightModel, FlightState


def make_model(**overrides: float) -> FlightModel:
    config = replace(
        DEFAULT_FLIGHT_CONFIG,
        start_altitude_m=2.0,
        glide_accel_mps2=10.0,
        glide_sink_mps=10.0,
        step_s=0.1,
        max_frame_s=0.1,
    )
    if overrides:
        config = replace(config, **overrides)
    return FlightModel(config)


def test_initial_state_is_high_level_and_rested() -> None:
    model = FlightModel(DEFAULT_FLIGHT_CONFIG)
    state = model.initial_state()
    assert state.x_m == 0.0
    assert state.altitude_m == DEFAULT_FLIGHT_CONFIG.start_altitude_m
    assert state.vertical_speed_mps == 0.0
    assert state.stamina == DEFAULT_FLIGHT_CONFIG.stamina_max
    assert state.cooldown_s == 0.0
    assert state.grounded is False


def test_gliding_moves_forward_and_descends() -> None:
    model = FlightModel(DEFAULT_FLIGHT_CONFIG)
    state = model.initial_state()
    previous_altitude = state.altitude_m
    previous_distance = state.distance_m

    for _ in range(50):
        state = model.advance(state, DEFAULT_FLIGHT_CONFIG.step_s)
        assert state.altitude_m < previous_altitude
        assert state.distance_m >= previous_distance
        assert 0.0 <= state.vertical_speed_mps <= DEFAULT_FLIGHT_CONFIG.glide_sink_mps
        previous_altitude = state.altitude_m
        previous_distance = state.distance_m


def test_glide_speed_converges_to_terminal_sink() -> None:
    model = make_model(start_altitude_m=10_000.0)
    state = model.initial_state()
    for _ in range(200):
        state = model.advance(state, 0.1)
    assert state.vertical_speed_mps == pytest.approx(10.0)


def test_vertical_speed_is_capped_at_terminal_sink() -> None:
    model = make_model()
    state = replace(model.initial_state(), vertical_speed_mps=99.0)
    advanced = model.advance(state, 0.1)
    assert advanced.vertical_speed_mps == pytest.approx(10.0)


def test_zero_or_negative_dt_changes_nothing() -> None:
    model = make_model()
    state = model.initial_state()
    assert model.advance(state, 0.0) is state
    assert model.advance(state, -1.0) is state


def test_flap_is_accepted_and_lifts_the_bird() -> None:
    model = make_model()
    state = model.initial_state()
    start_altitude = state.altitude_m

    flapped, accepted = model.flap(state)

    assert accepted is True
    assert flapped.x_m == state.x_m
    assert flapped.altitude_m == state.altitude_m
    assert flapped.vertical_speed_mps == -DEFAULT_FLIGHT_CONFIG.flap_up_speed_mps
    assert flapped.stamina == state.stamina - DEFAULT_FLIGHT_CONFIG.flap_stamina_cost
    assert flapped.cooldown_s == DEFAULT_FLIGHT_CONFIG.flap_cooldown_s

    for _ in range(5):
        flapped = model.advance(flapped, 0.1)
    assert flapped.altitude_m > start_altitude


def test_flap_during_cooldown_is_rejected() -> None:
    model = make_model()
    flapped, _ = model.flap(model.initial_state())

    rejected, accepted = model.flap(flapped)

    assert accepted is False
    assert rejected is flapped
    assert rejected.stamina == flapped.stamina


def test_cooldown_expires_and_allows_another_flap() -> None:
    model = make_model()
    state, _ = model.flap(model.initial_state())
    for _ in range(3):
        state = model.advance(state, 0.1)

    assert state.cooldown_s == 0.0
    _, accepted = model.flap(state)
    assert accepted is True


def test_stamina_can_be_spent_exactly_to_zero() -> None:
    model = make_model(stamina_max=20.0, flap_stamina_cost=20.0)
    state = model.initial_state()

    flapped, accepted = model.flap(state)

    assert accepted is True
    assert flapped.stamina == 0.0


def test_flap_without_stamina_is_rejected() -> None:
    model = make_model()
    state = replace(
        model.initial_state(),
        stamina=DEFAULT_FLIGHT_CONFIG.flap_stamina_cost - 0.01,
    )

    rejected, accepted = model.flap(state)

    assert accepted is False
    assert rejected is state


def test_stamina_does_not_regenerate() -> None:
    model = make_model()
    state, _ = model.flap(model.initial_state())
    stamina_after_flap = state.stamina
    for _ in range(100):
        state = model.advance(state, 0.1)
    assert state.stamina == stamina_after_flap


def test_touchdown_freezes_the_state() -> None:
    model = make_model(start_altitude_m=0.5)
    state = model.initial_state()

    for _ in range(3):
        state = model.advance(state, 0.1)

    assert state.grounded is True
    assert state.altitude_m == 0.0
    assert state.vertical_speed_mps == 0.0
    assert state.cooldown_s == 0.0
    assert state.distance_m > 0

    frozen = model.advance(state, 1.0)
    assert frozen is state
    rejected, accepted = model.flap(state)
    assert accepted is False
    assert rejected is state


def test_flap_without_stamina_after_touchdown_is_rejected() -> None:
    model = make_model(start_altitude_m=0.1, stamina_max=100.0)
    state = model.initial_state()
    state = model.advance(state, 1.0)
    assert state.grounded is True

    _, accepted = model.flap(state)
    assert accepted is False


def test_distance_is_reported_in_whole_metres() -> None:
    state = FlightState(
        x_m=12.99,
        altitude_m=10.0,
        vertical_speed_mps=0.0,
        stamina=100.0,
        cooldown_s=0.0,
    )
    assert state.distance_m == 12


@settings(max_examples=100, deadline=None)
@given(
    actions=st.lists(
        st.tuples(st.floats(min_value=0.0, max_value=0.5), st.booleans()),
        min_size=1,
        max_size=40,
    )
)
def test_invariants_hold_for_any_command_sequence(
    actions: list[tuple[float, bool]],
) -> None:
    model = make_model(start_altitude_m=5.0)
    state = model.initial_state()
    previous_distance = state.distance_m

    for dt, should_flap in actions:
        if should_flap:
            state, _ = model.flap(state)
        state = model.advance(state, dt)
        assert 0.0 <= state.stamina <= model.config.stamina_max
        assert state.altitude_m >= 0.0
        assert state.distance_m >= previous_distance
        previous_distance = state.distance_m


@settings(max_examples=50, deadline=None)
@given(
    actions=st.lists(
        st.tuples(st.floats(min_value=0.0, max_value=0.5), st.booleans()),
        min_size=1,
        max_size=40,
    )
)
def test_same_command_sequence_is_deterministic(
    actions: list[tuple[float, bool]],
) -> None:
    first = make_model(start_altitude_m=5.0)
    second = make_model(start_altitude_m=5.0)
    left = first.initial_state()
    right = second.initial_state()

    for dt, should_flap in actions:
        if should_flap:
            left, _ = first.flap(left)
            right, _ = second.flap(right)
        left = first.advance(left, dt)
        right = second.advance(right, dt)

    assert left == right
