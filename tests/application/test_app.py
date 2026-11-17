from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pygame
import pytest

from albatross.application.app import GameApp
from albatross.domain.config import DEFAULT_FLIGHT_CONFIG, FlightConfig
from albatross.domain.session import GamePhase, GameSession
from albatross.infrastructure.records import RecordStore
from albatross.presentation.audio import NullAudioBackend, SoundEngine
from albatross.presentation.i18n import Language
from albatross.presentation.renderer import Renderer

SIZE = (480, 270)


def make_config() -> FlightConfig:
    return replace(
        DEFAULT_FLIGHT_CONFIG,
        start_altitude_m=0.5,
        glide_accel_mps2=10.0,
        glide_sink_mps=10.0,
        step_s=0.1,
        max_frame_s=0.1,
    )


def make_app(tmp_path: Path) -> tuple[GameApp, RecordStore]:
    config = make_config()
    store = RecordStore(tmp_path / "record.json")
    app = GameApp(
        session=GameSession(config, best_distance_m=store.load_best()),
        renderer=Renderer(SIZE, config),
        sound=SoundEngine(NullAudioBackend()),
        store=store,
        screen=pygame.Surface(SIZE),
    )
    return app, store


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def click_event() -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)


def run_to_game_over(app: GameApp) -> None:
    for _ in range(20):
        app.tick([], 0.1)
        if app.session.state.phase is GamePhase.GAME_OVER:
            return
    raise AssertionError("the fast configuration should reach the ground")


def test_menu_renders_without_starting(tmp_path: Path) -> None:
    app, _ = make_app(tmp_path)

    assert app.tick([], 0.1) is True
    assert app.session.state.phase is GamePhase.MENU


def test_space_starts_a_run_and_flaps(tmp_path: Path) -> None:
    app, _ = make_app(tmp_path)

    app.tick([key_event(pygame.K_SPACE)], 0.1)
    assert app.session.state.phase is GamePhase.PLAYING

    distance = app.session.state.flight.distance_m
    stamina = app.session.state.flight.stamina
    app.tick([key_event(pygame.K_SPACE)], 0.1)
    assert app.session.state.flight.distance_m > distance
    assert app.session.state.flight.stamina < stamina


def test_click_starts_and_restarts(tmp_path: Path) -> None:
    app, _ = make_app(tmp_path)

    app.tick([click_event()], 0.1)
    assert app.session.state.phase is GamePhase.PLAYING

    run_to_game_over(app)
    app.tick([click_event()], 0.1)
    assert app.session.state.phase is GamePhase.PLAYING


def test_touchdown_persists_the_record(tmp_path: Path) -> None:
    app, store = make_app(tmp_path)

    app.tick([key_event(pygame.K_SPACE)], 0.1)
    run_to_game_over(app)

    state = app.session.state
    assert state.phase is GamePhase.GAME_OVER
    assert state.best_distance_m is not None
    assert store.load_best() == state.best_distance_m


def test_r_restarts_only_on_the_game_over_screen(tmp_path: Path) -> None:
    app, _ = make_app(tmp_path)
    app.tick([key_event(pygame.K_SPACE)], 0.1)

    app.tick([key_event(pygame.K_r)], 0.1)
    assert app.session.state.phase is GamePhase.PLAYING

    run_to_game_over(app)
    record = app.session.state.best_distance_m
    app.tick([key_event(pygame.K_r)], 0.1)
    assert app.session.state.phase is GamePhase.PLAYING
    assert app.session.state.best_distance_m == record
    assert app.session.state.flight.distance_m < (record or 0)


def test_escape_pauses_and_resumes(tmp_path: Path) -> None:
    app, _ = make_app(tmp_path)
    app.tick([key_event(pygame.K_SPACE)], 0.1)
    distance = app.session.state.flight.distance_m

    app.tick([key_event(pygame.K_ESCAPE)], 0.1)
    assert app.session.state.phase is GamePhase.PAUSED
    app.tick([], 1.0)
    assert app.session.state.flight.distance_m == distance

    app.tick([key_event(pygame.K_ESCAPE)], 0.1)
    assert app.session.state.phase is GamePhase.PLAYING


def test_language_and_sound_shortcuts(tmp_path: Path) -> None:
    app, _ = make_app(tmp_path)

    app.tick([key_event(pygame.K_l)], 0.1)
    assert app.translator.language is Language.EN
    app.tick([key_event(pygame.K_l)], 0.1)
    assert app.translator.language is Language.RU

    app.tick([key_event(pygame.K_m)], 0.1)
    assert app.sound.muted is True
    app.tick([key_event(pygame.K_m)], 0.1)
    assert app.sound.muted is False


def test_quit_request_stops_the_loop(tmp_path: Path) -> None:
    app, _ = make_app(tmp_path)

    assert app.tick([pygame.event.Event(pygame.QUIT)], 0.1) is False


def test_record_write_failure_does_not_crash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, store = make_app(tmp_path)

    def fail_save(best: int) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(store, "save_best", fail_save)
    app.tick([key_event(pygame.K_SPACE)], 0.1)
    run_to_game_over(app)

    assert app.session.state.phase is GamePhase.GAME_OVER
    assert not store.path.exists()
