from __future__ import annotations

import pygame
import pytest

from albatross.presentation import theme
from albatross.presentation.icon import ICON_SIZES, make_icon


def test_every_delivery_size_is_available() -> None:
    for size in ICON_SIZES:
        icon = make_icon(size)
        assert icon.get_size() == (size, size)
        assert icon.get_bounding_rect(min_alpha=1).width > size * 0.6


def test_icon_has_transparent_corners_and_opaque_centre() -> None:
    icon = make_icon(64)

    assert icon.get_at((0, 0)).a == 0
    assert icon.get_at((63, 0)).a == 0
    assert icon.get_at((32, 32)).a == 255


def test_icon_uses_bird_palette_at_native_resolution() -> None:
    icon = make_icon(64)
    colours = {
        icon.get_at((x, y))[:3] for x in range(64) for y in range(64) if icon.get_at((x, y)).a
    }

    assert theme.BIRD_BODY in colours
    assert theme.BIRD_SHADE in colours
    assert theme.BIRD_BEAK in colours
    assert theme.BIRD_WINGTIP in colours
    assert len(colours) >= 8


def test_large_icon_scales_the_master_by_whole_pixels() -> None:
    icon = make_icon(128)

    for y in range(0, 128, 2):
        for x in range(0, 128, 2):
            block = {tuple(icon.get_at((x + dx, y + dy))) for dy in range(2) for dx in range(2)}
            assert len(block) == 1


def test_icon_generation_is_deterministic() -> None:
    assert pygame.image.tobytes(make_icon(48), "RGBA") == pygame.image.tobytes(
        make_icon(48), "RGBA"
    )


def test_tiny_icons_are_rejected_with_a_clear_error() -> None:
    with pytest.raises(ValueError, match="16"):
        make_icon(8)
