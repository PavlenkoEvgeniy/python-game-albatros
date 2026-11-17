from __future__ import annotations

from dataclasses import replace

from albatross.domain.config import DEFAULT_FLIGHT_CONFIG, FlightConfig
from albatross.domain.session import GamePhase, GameSession


def make_session(
    best: int | None = None,
    **overrides: float,
) -> GameSession:
    config = replace(
        DEFAULT_FLIGHT_CONFIG,
        start_altitude_m=0.5,
        glide_accel_mps2=10.0,
        glide_sink_mps=10.0,
        step_s=0.1,
        max_frame_s=0.1,
    )
    if overrides:
        config = replace(config, **overrides)
    return GameSession(config, best_distance_m=best)


def finish(session: GameSession) -> None:
    for _ in range(5):
        if session.state.phase is GamePhase.GAME_OVER:
            return
        session.advance(0.1)


def test_session_starts_in_the_menu() -> None:
    session = make_session(best=42)
    assert session.state.phase is GamePhase.MENU
    assert session.state.best_distance_m == 42
    assert session.state.last_distance_m is None
    assert session.state.flight.distance_m == 0


def test_start_moves_from_menu_to_playing() -> None:
    session = make_session()
    assert session.start() is True
    assert session.state.phase is GamePhase.PLAYING
    assert session.state.flight.stamina == session.config.stamina_max
    assert session.state.last_distance_m is None


def test_start_is_ignored_outside_the_menu() -> None:
    session = make_session()
    session.start()
    assert session.start() is False
    assert session.state.phase is GamePhase.PLAYING


def test_flap_only_works_while_playing() -> None:
    session = make_session()
    assert session.request_flap() is False

    session.start()
    assert session.request_flap() is True
    assert session.state.flight.stamina == session.config.stamina_max - (
        session.config.flap_stamina_cost
    )
    assert session.request_flap() is False

    session.toggle_pause()
    assert session.request_flap() is False


def test_flap_is_rejected_when_stamina_is_exhausted() -> None:
    session = make_session(stamina_max=20.0, flap_stamina_cost=20.0)
    session.start()
    assert session.request_flap() is True
    session.advance(0.3)
    assert session.state.flight.cooldown_s == 0.0
    assert session.request_flap() is False


def test_pause_freezes_the_flight() -> None:
    session = make_session()
    session.start()
    session.advance(0.1)
    frozen = session.state.flight

    assert session.toggle_pause() is True
    assert session.state.phase is GamePhase.PAUSED
    assert session.advance(1.0) is False
    assert session.state.flight == frozen

    assert session.toggle_pause() is True
    assert session.state.phase is GamePhase.PLAYING
    assert session.advance(0.1) is True
    assert session.state.flight != frozen


def test_pause_is_ignored_in_other_phases() -> None:
    session = make_session()
    assert session.toggle_pause() is False
    session.start()
    finish(session)
    assert session.state.phase is GamePhase.GAME_OVER
    assert session.toggle_pause() is False


def test_advance_is_ignored_outside_playing() -> None:
    session = make_session()
    assert session.advance(0.1) is False
    session.start()
    session.toggle_pause()
    assert session.advance(0.1) is False


def test_touchdown_ends_the_run_and_updates_the_record() -> None:
    session = make_session()
    session.start()
    finish(session)

    state = session.state
    assert state.phase is GamePhase.GAME_OVER
    assert state.flight.grounded is True
    assert state.last_distance_m == state.flight.distance_m
    assert state.best_distance_m == state.last_distance_m
    assert state.new_record is True
    assert session.advance(0.1) is False


def test_weaker_run_does_not_lower_the_record() -> None:
    session = make_session(best=10_000)
    session.start()
    finish(session)
    assert session.state.best_distance_m == 10_000
    assert session.state.last_distance_m is not None
    assert session.state.last_distance_m < 10_000
    assert session.state.new_record is False


def test_better_run_replaces_the_record() -> None:
    session = make_session(best=1)
    session.start()
    finish(session)
    assert session.state.best_distance_m == session.state.last_distance_m
    assert session.state.best_distance_m > 1
    assert session.state.new_record is True


def test_restart_after_game_over_starts_a_fresh_run() -> None:
    session = make_session()
    session.start()
    finish(session)
    record = session.state.best_distance_m

    assert session.restart() is True
    state = session.state
    assert state.phase is GamePhase.PLAYING
    assert state.flight.distance_m == 0
    assert state.flight.stamina == session.config.stamina_max
    assert state.flight.altitude_m == session.config.start_altitude_m
    assert state.best_distance_m == record
    assert state.last_distance_m is None
    assert state.new_record is False


def test_restart_is_ignored_outside_game_over() -> None:
    session = make_session()
    assert session.restart() is False
    session.start()
    assert session.restart() is False
    assert session.state.phase is GamePhase.PLAYING


def test_start_is_ignored_after_game_over() -> None:
    session = make_session()
    session.start()
    finish(session)
    assert session.start() is False
    assert session.state.phase is GamePhase.GAME_OVER


def test_custom_config_is_exposed() -> None:
    config = FlightConfig(start_altitude_m=3.0)
    session = GameSession(config)
    assert session.config == config
