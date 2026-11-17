"""Deterministic procedural pixel-art scenery.

Everything is generated at the logical resolution and cached. Static layers use
a local seeded RNG; drawing a frame allocates no new textures.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from albatross.presentation import theme
from albatross.presentation.camera import Camera

RIDGE_STEPS = 160


@dataclass(frozen=True, slots=True)
class Cloud:
    x_m: float
    altitude_m: float
    depth: float
    surface: pygame.Surface


@dataclass(frozen=True, slots=True)
class _RidgePalette:
    base: theme.RGB
    light: theme.RGB
    shadow: theme.RGB
    snow: theme.RGB | None = None


def _ridge_height(t: float, amplitude: float, phase: float) -> float:
    wave = 0.5 + 0.5 * math.sin(t * math.tau * 3.0 + phase)
    detail = 0.5 + 0.5 * math.sin(t * math.tau * 7.0 + phase * 2.0)
    return 0.20 + amplitude * (0.68 * wave + 0.32 * detail)


def _make_ridge(
    width: int,
    height: int,
    palette: _RidgePalette,
    phase: float,
    amplitude: float,
    seed: int,
) -> pygame.Surface:
    """Draw a tileable, stepped mountain layer with a few texture strata."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    rng = random.Random(seed)
    heights: list[int] = []
    for x in range(width):
        crest = height * _ridge_height(x / max(1, width - 1), amplitude, phase)
        heights.append(max(2, min(height - 1, round(height - crest))))
    heights[-1] = heights[0]

    for x, ridge_y in enumerate(heights):
        pygame.draw.rect(
            surface,
            palette.base,
            (x, ridge_y, 1, height - ridge_y),
        )

    # A lit crest makes the silhouette read as rock rather than a flat blob.
    for x in range(1, width - 1):
        previous = heights[x - 1]
        current = heights[x]
        if current < previous:
            start = current
        elif current > previous:
            start = previous
        else:
            continue
        for offset in range(2):
            y = start + offset
            if y < height:
                surface.set_at((x, y), palette.light if offset == 0 else palette.shadow)

    # Short, deterministic strata and scree flecks. They stay away from the
    # crest so the skyline remains clean and readable.
    streak_count = max(10, width // 26)
    for _ in range(streak_count):
        x = rng.randrange(width)
        top = heights[x] + rng.randrange(4, max(5, min(28, height - heights[x])))
        if top >= height:
            continue
        length = rng.randrange(2, 9)
        colour = palette.shadow if rng.random() < 0.55 else palette.light
        pygame.draw.rect(surface, colour, (x, top, length, 1))

    if palette.snow is not None:
        for x in range(width):
            ridge_y = heights[x]
            if ridge_y < round(height * 0.28) and (x + seed) % 5 < 2:
                depth = 1 + (x + seed) % 3
                pygame.draw.rect(
                    surface,
                    palette.snow,
                    (x, ridge_y, 1, min(depth, height - ridge_y)),
                )
    return surface


def _make_cloud(width: int, height: int, rng: random.Random) -> pygame.Surface:
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    puffs = (
        (0.02, 0.40, 0.52, 0.42),
        (0.18, 0.18, 0.48, 0.54),
        (0.44, 0.32, 0.43, 0.42),
        (0.12, 0.54, 0.72, 0.28),
    )
    for left, top, width_ratio, height_ratio in puffs:
        pygame.draw.rect(
            surface,
            theme.CLOUD_SHADE,
            pygame.Rect(
                round(width * left),
                round(height * top),
                max(2, round(width * width_ratio)),
                max(1, round(height * height_ratio)),
            ),
        )
    for left, top, width_ratio, height_ratio in puffs:
        pygame.draw.rect(
            surface,
            theme.CLOUD_LIGHT,
            pygame.Rect(
                round(width * left),
                round(height * top),
                max(2, round(width * width_ratio)),
                max(1, round(height * height_ratio * 0.5)),
            ),
        )
    if width > 34 and rng.random() < 0.8:
        pygame.draw.rect(
            surface,
            theme.CLOUD_LIGHT,
            (width // 3, height // 5, max(2, width // 4), max(1, height // 3)),
        )
    return surface


def _make_sun(radius: int) -> pygame.Surface:
    size = radius * 4
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    pygame.draw.circle(surface, theme.SUN_RING, center, radius)
    pygame.draw.circle(surface, theme.SUN_GLOW, center, max(2, round(radius * 0.72)))
    pygame.draw.circle(surface, theme.SUN_CORE, center, max(2, round(radius * 0.48)))
    return surface


def _make_ground_tile(width: int, height: int, seed: int) -> pygame.Surface:
    rng = random.Random(seed)
    surface = pygame.Surface((width, height))
    surface.fill(theme.GROUND_BOTTOM)
    grass_depth: list[int] = []
    for x in range(width):
        depth = 4 + (x * 7 + seed) % 3
        grass_depth.append(depth)
        pygame.draw.rect(surface, theme.GROUND_TOP, (x, 0, 1, depth))
        surface.set_at((x, depth), theme.GROUND_LINE)
        if x % 7 == 0:
            blade = 2 + (x * 11 + seed) % 4
            pygame.draw.rect(
                surface,
                theme.GROUND_LINE,
                (x, max(0, depth - blade), 1, blade),
            )
    for _ in range(max(8, width // 4)):
        x = rng.randrange(width)
        y = rng.randrange(max(grass_depth) + 2, min(height, max(grass_depth) + 25))
        colour = theme.GROUND_STONE if rng.random() < 0.55 else theme.GROUND_DARK
        length = rng.randrange(1, 4)
        pygame.draw.rect(surface, colour, (x, y, length, 1))
    for y in range(14, height, 9):
        shade = theme.GROUND_DARK if (y // 9) % 2 else theme.GROUND_BOTTOM
        pygame.draw.rect(surface, shade, (0, y, width, 2))
    return surface


class Scene:
    """Pre-renders static pixel layers and scrolls them with parallax."""

    def __init__(self, size: tuple[int, int], seed: int = 7) -> None:
        self._width, self._height = size
        self._rng = random.Random(seed)
        self._sky = theme.banded_gradient(
            self._width,
            self._height,
            theme.SKY_BANDS,
        )
        self._altitude_tints = self._make_altitude_tints()

        self._sun = _make_sun(max(5, round(self._height * 0.055)))
        self._sun_position = (round(self._width * 0.81), round(self._height * 0.16))

        self._far_width = self._width * 2
        self._far = _make_ridge(
            self._far_width,
            round(self._height * 0.48),
            _RidgePalette(
                theme.MOUNTAIN_FAR,
                theme.MOUNTAIN_FAR_LIGHT,
                theme.MOUNTAIN_SHADOW,
                theme.MOUNTAIN_SNOW,
            ),
            phase=0.4,
            amplitude=0.9,
            seed=seed + 1,
        )
        self._mid_width = self._width * 2
        self._mid = _make_ridge(
            self._mid_width,
            round(self._height * 0.37),
            _RidgePalette(
                theme.MOUNTAIN_MID,
                theme.MOUNTAIN_MID_LIGHT,
                theme.MOUNTAIN_SHADOW,
            ),
            phase=2.1,
            amplitude=1.0,
            seed=seed + 2,
        )
        self._near_width = self._width * 2
        self._near = _make_ridge(
            self._near_width,
            round(self._height * 0.23),
            _RidgePalette(
                theme.MOUNTAIN_NEAR,
                theme.MOUNTAIN_NEAR_LIGHT,
                theme.GROUND_DARK,
            ),
            phase=4.6,
            amplitude=0.8,
            seed=seed + 3,
        )
        self._cloud_span_m = 170.0
        self._clouds = self._make_clouds()
        self._ground_tile = _make_ground_tile(64, self._height + 64, seed + 4)

    def _make_altitude_tints(self) -> list[pygame.Surface]:
        tints: list[pygame.Surface] = []
        for level in range(6):
            overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
            for y in range(self._height):
                for x in range(self._width):
                    if theme.bayer_threshold(x, y) < level / 6.0:
                        overlay.set_at((x, y), (*theme.SKY_HIGH_ALTITUDE, 235))
            tints.append(overlay)
        return tints

    def _make_clouds(self) -> list[Cloud]:
        clouds: list[Cloud] = []
        for _ in range(16):
            cloud_width = self._rng.randint(24, 58)
            cloud_height = self._rng.randint(9, 22)
            clouds.append(
                Cloud(
                    x_m=self._rng.uniform(0.0, self._cloud_span_m),
                    altitude_m=self._rng.uniform(12.0, 132.0),
                    depth=self._rng.uniform(0.03, 0.10),
                    surface=_make_cloud(cloud_width, cloud_height, self._rng),
                )
            )
        return clouds

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        surface.blit(self._sky, (0, 0))
        tint_level = min(5, round(5 * theme.clamp01(camera.altitude_m / 110.0)))
        if tint_level:
            surface.blit(self._altitude_tints[tint_level], (0, 0))
        sun_rect = self._sun.get_rect(center=self._sun_position)
        surface.blit(self._sun, sun_rect)

        for cloud in self._clouds:
            self._draw_cloud(surface, camera, cloud)

        horizon = round(self._height * 0.72)
        far_y = horizon - self._far.get_height() + round(self._height * 0.04)
        self._blit_tiled(surface, self._far, far_y, camera.parallax_offset(0.05))

        mid_base = min(camera.ground_y, self._height * 0.94) + 9
        self._blit_tiled(
            surface,
            self._mid,
            round(mid_base - self._mid.get_height()),
            camera.parallax_offset(0.18),
        )
        if camera.ground_y < self._height + 20:
            self._blit_tiled(
                surface,
                self._near,
                round(camera.ground_y - self._near.get_height() + 5),
                camera.parallax_offset(0.34),
            )

        self._draw_distant_birds(surface, camera)
        self._draw_ground(surface, camera)

    def _draw_cloud(self, surface: pygame.Surface, camera: Camera, cloud: Cloud) -> None:
        wrap_width = self._cloud_span_m * camera.pixels_per_meter + self._width
        x = (cloud.x_m - camera.x_m * cloud.depth) * camera.pixels_per_meter
        x = x % wrap_width - cloud.surface.get_width()
        y = camera.screen_y(cloud.altitude_m) - cloud.surface.get_height() / 2
        if -cloud.surface.get_width() < x < self._width and -cloud.surface.get_height() < y:
            surface.blit(cloud.surface, (round(x), round(y)))

    def _blit_tiled(
        self,
        surface: pygame.Surface,
        layer: pygame.Surface,
        y: float,
        offset: float,
    ) -> None:
        layer_width = layer.get_width()
        start = -(round(offset) % layer_width)
        x = start
        while x < self._width:
            surface.blit(layer, (x, round(y)))
            x += layer_width

    def _draw_distant_birds(self, surface: pygame.Surface, camera: Camera) -> None:
        for index, (world_x, altitude, size) in enumerate(
            ((40.0, 34.0, 3), (52.0, 37.0, 2), (67.0, 31.0, 2))
        ):
            x = camera.screen_x(world_x) + camera.parallax_offset(0.02) * (index + 1) * 0.1
            y = camera.screen_y(altitude)
            if -10 < x < self._width + 10 and -10 < y < self._height:
                points = [
                    (round(x - size), round(y)),
                    (round(x), round(y - size)),
                    (round(x + size), round(y)),
                ]
                pygame.draw.lines(surface, theme.MOUNTAIN_NEAR, False, points, 1)

    def _draw_ground(self, surface: pygame.Surface, camera: Camera) -> None:
        ground_y = camera.ground_y
        if ground_y >= self._height + 10:
            return

        top = round(ground_y)
        tile_width = self._ground_tile.get_width()
        shift = round(camera.parallax_offset(1.0)) % tile_width
        x = -shift
        while x < self._width:
            surface.blit(self._ground_tile, (x, top))
            x += tile_width
        if top + self._ground_tile.get_height() < self._height:
            pygame.draw.rect(
                surface,
                theme.GROUND_DARK,
                (0, top + self._ground_tile.get_height(), self._width, self._height),
            )
