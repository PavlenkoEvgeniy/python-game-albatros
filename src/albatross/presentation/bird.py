"""Indexed pixel-art albatross with wing and pitch poses."""

from __future__ import annotations

import math

import pygame

from albatross.presentation import theme

FLAP_DURATION_S = 0.32
DRAW_SIZE = (48, 32)
GRID_SIZE = (48, 32)

_EMPTY = 0
_BODY = 1
_SHADE = 2
_DARK = 3
_BEAK = 4
_EYE = 5

_PALETTE: dict[int, theme.RGBA] = {
    _EMPTY: (0, 0, 0, 0),
    _BODY: (*theme.BIRD_BODY, 255),
    _SHADE: (*theme.BIRD_SHADE, 255),
    _DARK: (*theme.BIRD_WINGTIP, 255),
    _BEAK: (*theme.BIRD_BEAK, 255),
    _EYE: (*theme.BIRD_EYE, 255),
}

Grid = list[list[int]]


def _polygon(grid: Grid, points: list[tuple[float, float]], value: int) -> None:
    """Fill an integer-index polygon with a simple scanline rasterizer."""
    if not points:
        return
    height = len(grid)
    width = len(grid[0])
    top = max(0, math.floor(min(y for _, y in points)))
    bottom = min(height - 1, math.ceil(max(y for _, y in points)))
    for y in range(top, bottom + 1):
        scan_y = y + 0.5
        crossings: list[float] = []
        for index, (x1, y1) in enumerate(points):
            x2, y2 = points[(index + 1) % len(points)]
            if (y1 <= scan_y < y2) or (y2 <= scan_y < y1):
                ratio = (scan_y - y1) / (y2 - y1)
                crossings.append(x1 + ratio * (x2 - x1))
        crossings.sort()
        for start, end in zip(crossings[::2], crossings[1::2], strict=False):
            left = max(0, math.ceil(start - 0.5))
            right = min(width - 1, math.floor(end - 0.5))
            for x in range(left, right + 1):
                grid[y][x] = value


def _circle(grid: Grid, cx: int, cy: int, radius: int, value: int) -> None:
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (
                (x - cx) ** 2 + (y - cy) ** 2 <= radius**2
                and 0 <= y < len(grid)
                and 0 <= x < len(grid[0])
            ):
                grid[y][x] = value


def _outline(grid: Grid) -> None:
    height = len(grid)
    width = len(grid[0])
    edge: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            if grid[y][x] == _EMPTY:
                continue
            neighbours = ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if any(
                nx < 0 or nx >= width or ny < 0 or ny >= height or grid[ny][nx] == _EMPTY
                for nx, ny in neighbours
            ):
                edge.append((x, y))
    for x, y in edge:
        grid[y][x] = _DARK


def _frame(wing_lift: float, pitch_slope: float) -> Grid:
    width, height = GRID_SIZE
    grid = [[_EMPTY for _ in range(width)] for _ in range(height)]
    cx, cy = 25, 16

    # Tail and far wing sit behind the body.
    _polygon(
        grid,
        [(cx - 19, cy + 1), (cx - 25, cy - 4), (cx - 23, cy + 4)],
        _SHADE,
    )
    _polygon(
        grid,
        [
            (cx - 3, cy - 1),
            (cx - 16, cy - 7 + wing_lift * 7),
            (cx - 25, cy - 9 + wing_lift * 14),
            (cx - 18, cy + 1 + wing_lift * 4),
            (cx - 5, cy + 3),
        ],
        _DARK,
    )

    _polygon(
        grid,
        [
            (cx - 21, cy + 1),
            (cx - 18, cy - 4),
            (cx + 2, cy - 6),
            (cx + 10, cy - 3),
            (cx + 12, cy + 1),
            (cx + 5, cy + 5),
            (cx - 19, cy + 5),
        ],
        _BODY,
    )
    _circle(grid, cx + 10, cy - 5, 4, _BODY)
    _polygon(
        grid,
        [(cx + 14, cy - 5), (cx + 20, cy - 4), (cx + 14, cy - 2)],
        _BEAK,
    )
    _polygon(
        grid,
        [
            (cx - 2, cy - 1),
            (cx - 16, cy - 10 + wing_lift * 9),
            (cx - 25, cy - 11 + wing_lift * 16),
            (cx - 17, cy + 2 + wing_lift * 5),
            (cx - 4, cy + 4),
        ],
        _SHADE,
    )
    _polygon(
        grid,
        [
            (cx - 25, cy - 11 + wing_lift * 16),
            (cx - 20, cy - 8 + wing_lift * 12),
            (cx - 21, cy - 5 + wing_lift * 13),
        ],
        _DARK,
    )
    _circle(grid, cx + 12, cy - 6, 1, _EYE)
    _outline(grid)

    if pitch_slope:
        sheared = [[_EMPTY for _ in range(width)] for _ in range(height)]
        for y in range(height):
            for x in range(width):
                if grid[y][x] == _EMPTY:
                    continue
                target_y = y + round((x - cx) * pitch_slope)
                if 0 <= target_y < height:
                    sheared[target_y][x] = grid[y][x]
        return sheared
    return grid


def _surface(grid: Grid) -> pygame.Surface:
    height = len(grid)
    width = len(grid[0])
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            if value != _EMPTY:
                surface.set_at((x, y), _PALETTE[value])
    return surface


class Bird:
    """Animation state and cached pixel sprites for the player's albatross."""

    def __init__(self) -> None:
        self._flap_timer = 0.0
        self._time = 0.0
        self._sprites: dict[tuple[int, int], pygame.Surface] = {}

    @property
    def flapping(self) -> bool:
        return self._flap_timer > 0.0

    @property
    def wing_lift(self) -> float:
        """``-1`` is fully raised, ``+1`` is fully lowered."""
        if self._flap_timer > 0.0:
            progress = 1.0 - self._flap_timer / FLAP_DURATION_S
            return math.sin(progress * math.tau) * 0.95
        return -0.12 + 0.06 * math.sin(self._time * 1.7)

    def notify_flap(self) -> None:
        self._flap_timer = FLAP_DURATION_S

    def update(self, dt: float) -> None:
        self._time += max(0.0, dt)
        self._flap_timer = max(0.0, self._flap_timer - max(0.0, dt))

    def draw(self, surface: pygame.Surface, center: tuple[int, int], vertical_speed: float) -> None:
        """Draw the cached bird sprite, quantizing its pitch to three poses."""
        image = self._sprite_for(self.wing_lift, vertical_speed)
        surface.blit(image, image.get_rect(center=center))

    def _sprite_for(self, wing_lift: float, vertical_speed: float) -> pygame.Surface:
        phase = 0 if wing_lift < -0.35 else 1 if wing_lift < 0.10 else 2 if wing_lift < 0.55 else 3
        pitch = -1 if vertical_speed < -2.0 else 1 if vertical_speed > 2.0 else 0
        key = (phase, pitch)
        sprite = self._sprites.get(key)
        if sprite is None:
            lift = (-0.9, -0.2, 0.35, 0.9)[phase]
            sprite = _surface(_frame(lift, pitch * 0.13))
            self._sprites[key] = sprite
        return sprite
