from __future__ import annotations

import pygame

from albatross.presentation.bird import FLAP_DURATION_S, Bird


def test_gliding_wing_lift_stays_subtle() -> None:
    bird = Bird()
    for _ in range(120):
        assert -0.2 <= bird.wing_lift <= 0.0
        bird.update(0.016)


def test_flap_animation_runs_and_finishes() -> None:
    bird = Bird()
    bird.notify_flap()
    assert bird.flapping is True

    lifts: list[float] = []
    for _ in range(40):
        lifts.append(bird.wing_lift)
        bird.update(FLAP_DURATION_S / 20)

    assert max(lifts) > 0.5
    assert bird.flapping is False


def test_update_ignores_negative_time() -> None:
    bird = Bird()
    bird.notify_flap()
    bird.update(-1.0)
    assert bird.flapping is True


def test_draw_produces_visible_pixels() -> None:
    bird = Bird()
    surface = pygame.Surface((400, 300), pygame.SRCALPHA)

    bird.draw(surface, (200, 150), vertical_speed=0.0)

    bounds = surface.get_bounding_rect(min_alpha=1)
    assert bounds.width > 0
    assert bounds.height > 0


def test_draw_handles_extreme_vertical_speeds() -> None:
    bird = Bird()
    surface = pygame.Surface((400, 300), pygame.SRCALPHA)
    bird.draw(surface, (200, 150), vertical_speed=-100.0)
    bird.draw(surface, (200, 150), vertical_speed=100.0)
    assert surface.get_bounding_rect(min_alpha=1).width > 0
