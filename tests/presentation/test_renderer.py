from __future__ import annotations

from dataclasses import replace

import pygame
import pytest

from albatross.domain.config import DEFAULT_FLIGHT_CONFIG, FlightConfig
from albatross.domain.session import GamePhase, GameSession
from albatross.presentation.i18n import Language, Translator
from albatross.presentation.renderer import Renderer

SIZE = (640, 360)


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


def test_world_is_scaled_with_uniform_pixel_blocks() -> None:
    config = make_config()
    renderer = Renderer(SIZE, config)
    session = GameSession(config)

    frame = renderer.render(session.state, 0.0, Translator(), muted=False)

    for block_y in range(80, 140, 4):
        for block_x in range(4, 44, 4):
            colours = {
                tuple(frame.get_at((block_x + dx, block_y + dy)))
                for dy in range(4)
                for dx in range(4)
            }
            assert len(colours) == 1


def test_renderer_does_not_mutate_the_session_state() -> None:
    config = make_config()
    session = GameSession(config)
    renderer = Renderer(SIZE, config)
    session.start()
    before = session.state

    renderer.render(session.state, 0.1, Translator(), muted=False)
    renderer.render(session.state, 0.1, Translator(), muted=False)

    assert session.state == before


def test_renderer_rejects_dimensions_off_the_pixel_grid() -> None:
    config = make_config()

    with pytest.raises(ValueError, match="multiples"):
        Renderer((481, 300), config)


def test_flap_streak_is_drawn_only_while_its_timer_is_alive() -> None:
    config = make_config()
    renderer = Renderer(SIZE, config)
    renderer._scene_surface.fill((0, 0, 0))

    renderer._streak_timer_s = 0.0
    renderer._draw_streaks((100, 80))
    clean = pygame.image.tobytes(renderer._scene_surface, "RGB")

    renderer._streak_timer_s = 0.2
    renderer._draw_streaks((100, 80))
    streaked = pygame.image.tobytes(renderer._scene_surface, "RGB")

    assert streaked != clean
