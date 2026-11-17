"""Limited palette and small pixel-art drawing helpers."""

from __future__ import annotations

import math
from collections.abc import Sequence

import pygame

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
PIXEL_SCALE = 4

# A deliberately small, warm-to-cold palette. Static surfaces only contain
# these colours (plus transparency); dithering supplies the apparent blends.
SKY_TOP: RGB = (15, 29, 55)
SKY_UPPER: RGB = (24, 43, 71)
SKY_MID: RGB = (43, 64, 89)
SKY_LOW: RGB = (111, 107, 108)
SKY_HORIZON: RGB = (205, 151, 118)
SKY_HIGH_ALTITUDE: RGB = (8, 16, 34)
SKY_BANDS: tuple[RGB, ...] = (
    SKY_TOP,
    (22, 40, 68),
    (31, 52, 80),
    (43, 64, 89),
    (58, 76, 97),
    (79, 90, 103),
    (105, 103, 108),
    (145, 121, 111),
    SKY_HORIZON,
)

SUN_CORE: RGB = (255, 232, 176)
SUN_GLOW: RGB = (244, 198, 132)
SUN_RING: RGB = (190, 137, 101)

MOUNTAIN_FAR: RGB = (101, 119, 142)
MOUNTAIN_FAR_LIGHT: RGB = (129, 143, 158)
MOUNTAIN_MID: RGB = (66, 84, 107)
MOUNTAIN_MID_LIGHT: RGB = (88, 104, 123)
MOUNTAIN_NEAR: RGB = (37, 52, 72)
MOUNTAIN_NEAR_LIGHT: RGB = (54, 70, 88)
MOUNTAIN_SHADOW: RGB = (31, 43, 60)
MOUNTAIN_SNOW: RGB = (183, 190, 190)

GROUND_TOP: RGB = (57, 79, 62)
GROUND_LIGHT: RGB = (89, 112, 77)
GROUND_LINE: RGB = (137, 157, 105)
GROUND_BOTTOM: RGB = (26, 38, 39)
GROUND_DARK: RGB = (18, 28, 30)
GROUND_STONE: RGB = (77, 83, 75)

BIRD_BODY: RGB = (246, 241, 219)
BIRD_SHADE: RGB = (190, 199, 197)
BIRD_WINGTIP: RGB = (29, 35, 44)
BIRD_BEAK: RGB = (232, 155, 66)
BIRD_EYE: RGB = (24, 28, 34)

TEXT: RGB = (250, 244, 225)
TEXT_MUTED: RGB = (196, 202, 199)
TEXT_SHADOW: RGB = (8, 12, 19)
ACCENT: RGB = (255, 207, 98)
NEW_RECORD: RGB = (255, 232, 150)

PANEL: RGBA = (11, 18, 28, 224)
PANEL_INNER: RGBA = (22, 32, 43, 224)
PANEL_BORDER: RGBA = (228, 211, 168, 180)
STAMINA_TRACK: RGBA = (12, 20, 25, 235)
STAMINA_FILL: RGB = (244, 194, 82)
STAMINA_LOW: RGB = (220, 92, 75)
STAMINA_BORDER: RGBA = (230, 223, 194, 190)

CLOUD_LIGHT: RGB = (205, 202, 191)
CLOUD_SHADE: RGB = (151, 160, 165)
CLOUD: RGBA = (*CLOUD_LIGHT, 255)

BAYER_4: tuple[tuple[int, ...], ...] = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def snap(value: float, step: int = PIXEL_SCALE) -> int:
    """Round a screen coordinate to the nearest pixel-grid line."""
    return math.floor(value / step + 0.5) * step


def lerp_color(start: RGB, end: RGB, t: float) -> RGB:
    """Linear interpolation between two opaque colours."""
    amount = clamp01(t)
    return (
        round(start[0] + (end[0] - start[0]) * amount),
        round(start[1] + (end[1] - start[1]) * amount),
        round(start[2] + (end[2] - start[2]) * amount),
    )


def bayer_threshold(x: int, y: int) -> float:
    """Return the ordered-dither threshold in ``(0, 1)`` for a pixel."""
    return (BAYER_4[y % 4][x % 4] + 0.5) / 16.0


def dither_color(
    first: RGB,
    second: RGB,
    x: int,
    y: int,
    amount: float,
) -> RGB:
    """Choose one of two palette colours using an ordered 4x4 pattern.

    The squared amount keeps band interiors solid and concentrates the pattern
    near the transition, avoiding a full-screen checkerboard in large skies.
    """
    weight = clamp01(amount) ** 2
    return second if weight > bayer_threshold(x, y) else first


def banded_gradient(width: int, height: int, colors: Sequence[RGB]) -> pygame.Surface:
    """Pre-render a hard-banded vertical gradient with Bayer transitions.

    Only the supplied palette colours are emitted. Adjacent bands dither into
    one another, so increasing the image height does not create a new smooth
    ramp or any interpolated colours.
    """
    if width <= 0 or height <= 0:
        raise ValueError("gradient dimensions must be positive")
    if len(colors) < 2:
        raise ValueError("a gradient needs at least two colours")

    palette = tuple(colors)
    surface = pygame.Surface((width, height))
    last_row = max(1, height - 1)
    span = len(palette) - 1
    for y in range(height):
        position = (y / last_row) * span
        index = min(int(position), span - 1)
        fraction = position - index
        first = palette[index]
        second = palette[index + 1]
        for x in range(width):
            surface.set_at((x, y), dither_color(first, second, x, y, fraction))
    return surface


def vertical_gradient(width: int, height: int, top: RGB, bottom: RGB) -> pygame.Surface:
    """Pre-render a two-colour dithered gradient with exact endpoints."""
    return banded_gradient(width, height, (top, bottom))


def pixel_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: RGB | RGBA | None,
    *,
    border: RGB | RGBA | None = None,
    cut: int = 8,
    border_width: int = PIXEL_SCALE,
) -> None:
    """Draw a stepped rectangular panel with no curved or anti-aliased edges."""
    cut = max(0, min(cut, rect.width // 2, rect.height // 2))
    points = [
        (rect.left + cut, rect.top),
        (rect.right - cut, rect.top),
        (rect.right, rect.top + cut),
        (rect.right, rect.bottom - cut),
        (rect.right - cut, rect.bottom),
        (rect.left + cut, rect.bottom),
        (rect.left, rect.bottom - cut),
        (rect.left, rect.top + cut),
    ]
    if color is not None:
        pygame.draw.polygon(surface, color, points)
    if border is not None:
        pygame.draw.lines(surface, border, True, points, border_width)


def rounded_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: RGB | RGBA,
    radius: int = 12,
    width: int = 0,
) -> None:
    """Compatibility helper for callers that still want a simple rectangle."""
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)
