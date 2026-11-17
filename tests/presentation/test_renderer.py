from __future__ import annotations

from dataclasses import replace

import pygame

from albatross.domain.config import DEFAULT_FLIGHT_CONFIG, FlightConfig
from albatross.domain.session import GamePhase, GameSession
from albatross.presentation.i18n import Language, Translator
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


def test_renders_every_phase() -> None:
    config = make_config()
    session = GameSession(config)
    renderer = Renderer(SIZE, config)
    translator = Translator()

    menu = renderer.render(session.state, 0.016, translator, muted=False)
    assert menu.get_size() == SIZE

    session.start()
    renderer.notify_flap()
    playing = renderer.render(session.state, 0.016, translator, muted=False)
    assert playing.get_size() == SIZE

    session.toggle_pause()
    paused = renderer.render(session.state, 0.016, translator, muted=True)
    assert paused.get_size() == SIZE

    session.toggle_pause()
    for _ in range(10):
        session.advance(0.1)
    assert session.state.phase is GamePhase.GAME_OVER
    over = renderer.render(session.state, 0.016, translator, muted=False)
    assert over.get_size() == SIZE


def test_renderer_handles_negative_dt_and_english() -> None:
    config = make_config()
    session = GameSession(config)
    renderer = Renderer(SIZE, config)

    frame = renderer.render(session.state, -1.0, Translator(Language.EN), muted=True)

    assert isinstance(frame, pygame.Surface)
    assert frame.get_size() == SIZE
