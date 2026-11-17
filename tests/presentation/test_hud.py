from __future__ import annotations

import pygame

from albatross.domain.config import DEFAULT_FLIGHT_CONFIG
from albatross.domain.flight import FlightState
from albatross.domain.session import GamePhase, SessionState
from albatross.presentation.hud import Hud
from albatross.presentation.i18n import Translator

SIZE = (640, 360)
BAR_POINTS = [(x, y) for x in range(48, 340, 8) for y in range(50, 76, 4)]


def make_state(
    *,
    distance_m: float = 10.0,
    stamina: float = 100.0,
    best: int | None = 500,
    phase: GamePhase = GamePhase.PLAYING,
    new_record: bool = False,
) -> SessionState:
    flight = FlightState(
        x_m=distance_m,
        altitude_m=20.0,
        vertical_speed_mps=0.0,
        stamina=stamina,
        cooldown_s=0.0,
    )
    return SessionState(
        phase=phase,
        flight=flight,
        best_distance_m=best,
        last_distance_m=round(distance_m) if phase is GamePhase.GAME_OVER else None,
        new_record=new_record,
    )


def draw(state: SessionState, muted: bool = False) -> pygame.Surface:
    surface = pygame.Surface(SIZE, pygame.SRCALPHA)
    Hud(DEFAULT_FLIGHT_CONFIG, SIZE).draw(surface, state, Translator(), muted, 0.5)
    return surface


def test_stamina_bar_shows_full_and_empty_states() -> None:
    full = draw(make_state(stamina=100.0))
    empty = draw(make_state(stamina=0.0))

    assert any(full.get_at(point) != empty.get_at(point) for point in BAR_POINTS)


def test_stamina_above_max_is_clamped_to_the_track() -> None:
    overfilled = draw(make_state(stamina=250.0))
    full = draw(make_state(stamina=100.0))

    assert pygame.image.tobytes(overfilled, "RGBA") == pygame.image.tobytes(full, "RGBA")
    assert overfilled.get_at((350, 60)).a == 0


def test_distance_change_redraws_the_hud() -> None:
    near = draw(make_state(distance_m=10.0))
    far = draw(make_state(distance_m=99_999.0))

    assert pygame.image.tobytes(near, "RGBA") != pygame.image.tobytes(far, "RGBA")


def test_record_placeholder_is_rendered() -> None:
    without_record = draw(make_state(best=None))
    with_record = draw(make_state(best=1234))

    assert pygame.image.tobytes(without_record, "RGBA") != pygame.image.tobytes(with_record, "RGBA")


def test_new_record_line_changes_the_game_over_screen() -> None:
    regular = draw(make_state(phase=GamePhase.GAME_OVER, best=100, new_record=False))
    record = draw(make_state(phase=GamePhase.GAME_OVER, best=100, new_record=True))

    assert pygame.image.tobytes(regular, "RGBA") != pygame.image.tobytes(record, "RGBA")


def test_sound_status_and_pause_overlay_render() -> None:
    muted = draw(make_state(), muted=True)
    unmuted = draw(make_state(), muted=False)
    paused = draw(make_state(phase=GamePhase.PAUSED))

    assert pygame.image.tobytes(muted, "RGBA") != pygame.image.tobytes(unmuted, "RGBA")
    assert pygame.image.tobytes(paused, "RGBA") != pygame.image.tobytes(unmuted, "RGBA")
