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
# Modern sunset ramp: deep indigo through violet and coral into amber.
SKY_TOP: RGB = (18, 14, 48)
SKY_UPPER: RGB = (29, 22, 72)
SKY_MID: RGB = (47, 33, 92)
SKY_LOW: RGB = (84, 55, 112)
SKY_HORIZON: RGB = (252, 178, 118)
SKY_HIGH_ALTITUDE: RGB = (10, 7, 26)
SKY_BANDS: tuple[RGB, ...] = (
    SKY_TOP,
    (26, 20, 64),
    (38, 27, 80),
    (52, 34, 92),
    (74, 46, 104),
    (104, 60, 108),
    (136, 76, 106),
    (171, 94, 100),
    (206, 116, 92),
    (243, 152, 98),
    SKY_HORIZON,
)

SUN_CORE: RGB = (255, 238, 196)
SUN_GLOW: RGB = (255, 172, 98)
SUN_RING: RGB = (233, 116, 78)

MOUNTAIN_FAR: RGB = (97, 84, 140)
MOUNTAIN_FAR_LIGHT: RGB = (128, 112, 160)
MOUNTAIN_MID: RGB = (64, 56, 112)
MOUNTAIN_MID_LIGHT: RGB = (94, 82, 138)
MOUNTAIN_NEAR: RGB = (36, 34, 80)
MOUNTAIN_NEAR_LIGHT: RGB = (58, 54, 106)
MOUNTAIN_SHADOW: RGB = (28, 26, 68)
MOUNTAIN_SNOW: RGB = (222, 210, 232)
MOUNTAIN_HAZE: RGB = (176, 132, 152)

GROUND_TOP: RGB = (46, 84, 70)
GROUND_LIGHT: RGB = (76, 118, 84)
GROUND_LINE: RGB = (134, 170, 106)
GROUND_BOTTOM: RGB = (24, 36, 36)
GROUND_DARK: RGB = (16, 26, 28)
GROUND_STONE: RGB = (70, 76, 74)
GRASS_DEEP: RGB = (32, 58, 50)

BIRD_BODY: RGB = (250, 244, 226)
BIRD_SHADE: RGB = (206, 178, 192)
BIRD_WINGTIP: RGB = (34, 28, 58)
BIRD_BEAK: RGB = (255, 152, 72)
BIRD_EYE: RGB = (20, 16, 34)

TEXT: RGB = (250, 244, 225)
TEXT_MUTED: RGB = (196, 202, 199)
TEXT_SHADOW: RGB = (8, 12, 19)
ACCENT: RGB = (255, 207, 98)
NEW_RECORD: RGB = (255, 232, 150)

PANEL: RGBA = (16, 14, 42, 224)
PANEL_INNER: RGBA = (30, 24, 60, 224)
PANEL_BORDER: RGBA = (228, 211, 168, 180)
STAMINA_TRACK: RGBA = (14, 12, 36, 235)
STAMINA_FILL: RGB = (244, 194, 82)
STAMINA_LOW: RGB = (220, 92, 75)
STAMINA_BORDER: RGBA = (230, 223, 194, 190)

CLOUD_LIGHT: RGB = (255, 198, 142)
CLOUD_SHADE: RGB = (172, 96, 130)
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
