from __future__ import annotations

import pygame

from albatross.presentation import theme


def test_clamp_stays_in_range() -> None:
    assert theme.clamp01(-1.0) == 0.0
    assert theme.clamp01(0.5) == 0.5
    assert theme.clamp01(2.0) == 1.0


def test_colour_interpolation_hits_both_ends() -> None:
    assert theme.lerp_color((0, 10, 20), (100, 110, 120), 0.0) == (0, 10, 20)
    assert theme.lerp_color((0, 10, 20), (100, 110, 120), 1.0) == (100, 110, 120)
    assert theme.lerp_color((0, 10, 20), (100, 110, 120), 2.0) == (100, 110, 120)


def test_gradient_changes_from_top_to_bottom() -> None:
    surface = theme.vertical_gradient(8, 32, (0, 0, 0), (200, 200, 200))
    assert isinstance(surface, pygame.Surface)
    assert surface.get_at((4, 0))[:3] == (0, 0, 0)
    assert surface.get_at((4, 31))[:3] == (200, 200, 200)


def test_rounded_rect_draws_inside_the_surface() -> None:
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    theme.rounded_rect(surface, pygame.Rect(4, 4, 32, 24), (255, 0, 0), radius=6)
    assert surface.get_at((20, 15)) == (255, 0, 0, 255)
