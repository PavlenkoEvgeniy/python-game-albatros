"""Colours, sizes and small drawing helpers for the procedural look."""

from __future__ import annotations

import pygame

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

SKY_TOP: RGB = (20, 42, 82)
SKY_HORIZON: RGB = (238, 190, 154)
SKY_HIGH_ALTITUDE: RGB = (8, 16, 38)

SUN_CORE: RGB = (255, 232, 176)
SUN_GLOW: RGB = (255, 198, 132)

MOUNTAIN_FAR: RGB = (118, 132, 158)
MOUNTAIN_MID: RGB = (82, 96, 124)
MOUNTAIN_NEAR: RGB = (48, 62, 86)

GROUND_TOP: RGB = (64, 88, 78)
GROUND_BOTTOM: RGB = (25, 38, 42)
GROUND_LINE: RGB = (122, 154, 128)

BIRD_BODY: RGB = (248, 248, 242)
BIRD_SHADE: RGB = (206, 212, 214)
BIRD_WINGTIP: RGB = (36, 40, 48)
BIRD_BEAK: RGB = (232, 164, 76)
BIRD_EYE: RGB = (30, 34, 40)

TEXT: RGB = (250, 248, 240)
TEXT_MUTED: RGB = (202, 208, 214)
TEXT_SHADOW: RGB = (10, 14, 22)
ACCENT: RGB = (255, 214, 120)
NEW_RECORD: RGB = (255, 232, 150)

PANEL: RGBA = (12, 18, 28, 196)
PANEL_BORDER: RGBA = (255, 255, 255, 36)
STAMINA_TRACK: RGBA = (18, 26, 34, 190)
STAMINA_FILL: RGB = (255, 198, 92)
STAMINA_LOW: RGB = (232, 104, 86)
STAMINA_BORDER: RGBA = (255, 255, 255, 48)

CLOUD: RGBA = (255, 250, 242, 150)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def lerp_color(start: RGB, end: RGB, t: float) -> RGB:
    """Linear interpolation between two opaque colours."""
    amount = clamp01(t)
    return (
        round(start[0] + (end[0] - start[0]) * amount),
        round(start[1] + (end[1] - start[1]) * amount),
        round(start[2] + (end[2] - start[2]) * amount),
    )


def vertical_gradient(width: int, height: int, top: RGB, bottom: RGB) -> pygame.Surface:
    """Pre-render a vertical gradient once."""
    surface = pygame.Surface((width, height))
    last_row = max(1, height - 1)
    for y in range(height):
        surface.fill(lerp_color(top, bottom, y / last_row), (0, y, width, 1))
    return surface


def rounded_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: RGB | RGBA,
    radius: int = 12,
    width: int = 0,
) -> None:
    """Draw a rounded rectangle with optional border."""
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)
