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


def test_banded_gradient_uses_only_supplied_palette() -> None:
    palette = ((10, 20, 30), (40, 50, 60), (80, 70, 60))
    surface = theme.banded_gradient(9, 35, palette)

    colours = {surface.get_at((x, y))[:3] for x in range(9) for y in range(35)}
    assert colours == set(palette)


def test_dither_pattern_is_deterministic_and_repeating() -> None:
    left = [
        theme.dither_color((0, 0, 0), (255, 255, 255), x, y, 0.5)
        for y in range(4)
        for x in range(4)
    ]
    right = [
        theme.dither_color((0, 0, 0), (255, 255, 255), x, y, 0.5)
        for y in range(4)
        for x in range(4)
    ]

    assert left == right
    assert 0 < sum(colour[0] for colour in left) // 255 < 16


def test_snap_aligns_to_pixel_grid() -> None:
    assert theme.snap(31.9) == 32
    assert theme.snap(33.0) == 32
    assert theme.snap(34.0) == 36


def test_pixel_panel_cuts_corners_without_anti_aliasing() -> None:
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    theme.pixel_panel(
        surface,
        pygame.Rect(8, 8, 48, 32),
        (20, 30, 40, 255),
        border=(200, 210, 220, 255),
        cut=8,
    )

    assert surface.get_at((8, 8)).a == 0
    assert surface.get_at((12, 12)).a == 255
    assert surface.get_at((32, 24)).a == 255
