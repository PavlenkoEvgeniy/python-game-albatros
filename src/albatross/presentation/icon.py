"""Shared native-resolution pixel-art icon for the window and installers."""

from __future__ import annotations

import pygame

from albatross.presentation import theme

ICON_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


def _point(base: int, nx: float, ny: float) -> tuple[int, int]:
    return (round(nx * base), round(ny * base))


def _polygon(
    surface: pygame.Surface,
    base: int,
    points: tuple[tuple[float, float], ...],
    colour: theme.RGB,
) -> None:
    pygame.draw.polygon(
        surface,
        colour,
        [_point(base, x, y) for x, y in points],
    )


def _draw_badge(surface: pygame.Surface, base: int) -> None:
    cut = max(1, round(base * 0.14))
    for y in range(base):
        distance = min(y, base - 1 - y)
        inset = cut - distance if distance < cut else 0
        if y < round(base * 0.48):
            colour = theme.SKY_TOP
        elif y < round(base * 0.68):
            colour = theme.SKY_MID
        else:
            colour = theme.SKY_LOW
        pygame.draw.rect(surface, colour, (inset, y, base - inset * 2, 1))


def _draw_sun(surface: pygame.Surface, base: int) -> None:
    centre = _point(base, 0.74, 0.27)
    radius = max(2, round(base * 0.12))
    pygame.draw.circle(surface, theme.SUN_RING, centre, radius)
    pygame.draw.circle(surface, theme.SUN_GLOW, centre, max(1, round(radius * 0.72)))
    pygame.draw.circle(surface, theme.SUN_CORE, centre, max(1, round(radius * 0.46)))


def _draw_landscape(surface: pygame.Surface, base: int) -> None:
    _polygon(
        surface,
        base,
        (
            (0.00, 0.67),
            (0.16, 0.48),
            (0.30, 0.64),
            (0.46, 0.43),
            (0.66, 0.67),
            (0.82, 0.51),
            (1.00, 0.66),
            (1.00, 1.00),
            (0.00, 1.00),
        ),
        theme.MOUNTAIN_FAR,
    )
    _polygon(
        surface,
        base,
        (
            (0.00, 0.80),
            (0.18, 0.66),
            (0.34, 0.78),
            (0.55, 0.61),
            (0.73, 0.80),
            (0.90, 0.69),
            (1.00, 0.78),
            (1.00, 1.00),
            (0.00, 1.00),
        ),
        theme.MOUNTAIN_MID,
    )
    pygame.draw.rect(
        surface,
        theme.GROUND_TOP,
        (0, round(base * 0.88), base, base - round(base * 0.88)),
    )
    pygame.draw.rect(
        surface,
        theme.GROUND_LINE,
        (0, round(base * 0.88), base, max(1, round(base * 0.025))),
    )


def _draw_bird(surface: pygame.Surface, base: int) -> None:
    # Front-facing soaring silhouette: long narrow wings, a small body and the
    # unmistakable pale head. This stays legible even at 16 pixels.
    _polygon(
        surface,
        base,
        (
            (0.47, 0.43),
            (0.34, 0.30),
            (0.11, 0.20),
            (0.27, 0.42),
            (0.44, 0.53),
            (0.53, 0.50),
        ),
        theme.BIRD_SHADE,
    )
    _polygon(
        surface,
        base,
        (
            (0.11, 0.20),
            (0.23, 0.25),
            (0.29, 0.40),
        ),
        theme.BIRD_WINGTIP,
    )
    _polygon(
        surface,
        base,
        (
            (0.53, 0.43),
            (0.66, 0.30),
            (0.89, 0.20),
            (0.73, 0.42),
            (0.56, 0.53),
            (0.47, 0.50),
        ),
        theme.BIRD_SHADE,
    )
    _polygon(
        surface,
        base,
        (
            (0.89, 0.20),
            (0.77, 0.25),
            (0.71, 0.40),
        ),
        theme.BIRD_WINGTIP,
    )
    _polygon(
        surface,
        base,
        (
            (0.45, 0.43),
            (0.50, 0.41),
            (0.55, 0.43),
            (0.56, 0.63),
            (0.50, 0.70),
            (0.44, 0.63),
        ),
        theme.BIRD_BODY,
    )
    pygame.draw.circle(
        surface,
        theme.BIRD_BODY,
        _point(base, 0.53, 0.43),
        max(1, round(base * 0.055)),
    )
    _polygon(
        surface,
        base,
        ((0.57, 0.41), (0.64, 0.43), (0.57, 0.46)),
        theme.BIRD_BEAK,
    )
    pygame.draw.circle(
        surface,
        theme.BIRD_EYE,
        _point(base, 0.55, 0.405),
        max(1, base // 64),
    )


def _native_icon(base: int) -> pygame.Surface:
    surface = pygame.Surface((base, base), pygame.SRCALPHA)
    _draw_badge(surface, base)
    _draw_sun(surface, base)
    _draw_landscape(surface, base)
    _draw_bird(surface, base)
    return surface


def make_icon(size: int = 64) -> pygame.Surface:
    """Return a crisp icon at ``size``; large sizes scale a 64-pixel master."""
    if size < 16:
        raise ValueError("icons smaller than 16 pixels are not supported")
    base = 64 if size > 64 and size % 64 == 0 else size
    icon = _native_icon(base)
    if base == size:
        return icon
    scaled = pygame.transform.scale(icon, (size, size))
    return scaled
