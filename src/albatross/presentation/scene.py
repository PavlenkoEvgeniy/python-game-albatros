"""Procedural scenery: sky, sun, clouds, mountain layers and ground."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from albatross.presentation import theme
from albatross.presentation.camera import Camera


@dataclass(frozen=True, slots=True)
class Cloud:
    x_m: float
    altitude_m: float
    depth: float
    surface: pygame.Surface


def _make_ridge(
    width: int,
    height: int,
    color: theme.RGB,
    phase: float,
    amplitude: float,
) -> pygame.Surface:
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    steps = 96
    points: list[tuple[float, float]] = []
    for index in range(steps + 1):
        t = index / steps
        wave = 0.5 + 0.5 * math.sin(t * math.tau * 3.0 + phase)
        detail = 0.5 + 0.5 * math.sin(t * math.tau * 7.0 + phase * 2.0)
        crest = height * (0.22 + amplitude * (0.72 * wave + 0.28 * detail))
        points.append((width * t, height - crest))

    polygon = [(0, height), *points, (width, height)]
    pygame.draw.polygon(surface, color, polygon)
    pygame.draw.aalines(
        surface,
        theme.lerp_color(color, (255, 255, 255), 0.16),
        False,
        points,
    )
    return surface


def _make_cloud(width: int, height: int) -> pygame.Surface:
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    puffs = (
        (0.02, 0.42, 0.55, 0.55),
        (0.20, 0.18, 0.58, 0.72),
        (0.48, 0.32, 0.50, 0.60),
        (0.10, 0.60, 0.80, 0.38),
    )
    for left, top, width_ratio, height_ratio in puffs:
        rect = pygame.Rect(
            round(width * left),
            round(height * top),
            round(width * width_ratio),
            round(height * height_ratio),
        )
        pygame.draw.ellipse(surface, theme.CLOUD, rect)
    return surface


def _make_sun(radius: int) -> pygame.Surface:
    size = radius * 4
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    for step in range(radius, 0, -2):
        alpha = max(0, round(58 * (1.0 - step / radius) ** 2))
        pygame.draw.circle(
            surface,
            (*theme.SUN_GLOW, alpha),
            center,
            step,
        )
    pygame.draw.circle(surface, theme.SUN_CORE, center, max(4, radius // 3))
    return surface


class Scene:
    """Pre-renders static layers and scrolls them with parallax."""

    def __init__(self, size: tuple[int, int], seed: int = 7) -> None:
        self._width, self._height = size
        self._rng = random.Random(seed)
        self._sky = theme.vertical_gradient(
            self._width,
            self._height,
            theme.SKY_TOP,
            theme.SKY_HORIZON,
        )
        self._altitude_tint = pygame.Surface(size)
        self._altitude_tint.fill(theme.SKY_HIGH_ALTITUDE)
        self._altitude_tint.set_alpha(0)

        self._sun = _make_sun(round(self._height * 0.095))
        self._sun_position = (round(self._width * 0.79), round(self._height * 0.15))

        self._far_width = self._width * 2
        self._far = _make_ridge(
            self._far_width,
            round(self._height * 0.46),
            theme.MOUNTAIN_FAR,
            phase=0.4,
            amplitude=0.9,
        )
        self._mid_width = self._width * 2
        self._mid = _make_ridge(
            self._mid_width,
            round(self._height * 0.36),
            theme.MOUNTAIN_MID,
            phase=2.1,
            amplitude=1.0,
        )
        self._near_width = self._width * 2
        self._near = _make_ridge(
            self._near_width,
            round(self._height * 0.20),
            theme.MOUNTAIN_NEAR,
            phase=4.6,
            amplitude=0.8,
        )
        self._cloud_span_m = 170.0
        self._clouds = self._make_clouds()
        self._ground = theme.vertical_gradient(
            self._width,
            self._height,
            theme.GROUND_TOP,
            theme.GROUND_BOTTOM,
        )

    def _make_clouds(self) -> list[Cloud]:
        clouds: list[Cloud] = []
        for _ in range(16):
            cloud_width = self._rng.randint(46, 118)
            cloud_height = self._rng.randint(22, 52)
            clouds.append(
                Cloud(
                    x_m=self._rng.uniform(0.0, self._cloud_span_m),
                    altitude_m=self._rng.uniform(12.0, 132.0),
                    depth=self._rng.uniform(0.03, 0.10),
                    surface=_make_cloud(cloud_width, cloud_height),
                )
            )
        return clouds

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        surface.blit(self._sky, (0, 0))
        tint_alpha = round(72 * theme.clamp01(camera.altitude_m / 110.0))
        self._altitude_tint.set_alpha(tint_alpha)
        surface.blit(self._altitude_tint, (0, 0))
        surface.blit(self._sun, self._sun.get_rect(center=self._sun_position))

        for cloud in self._clouds:
            self._draw_cloud(surface, camera, cloud)

        horizon = round(self._height * 0.72)
        far_y = horizon - self._far.get_height() + round(self._height * 0.04)
        self._blit_tiled(surface, self._far, far_y, camera.parallax_offset(0.05))

        mid_base = min(camera.ground_y, self._height * 0.94) + 18
        self._blit_tiled(
            surface,
            self._mid,
            round(mid_base - self._mid.get_height()),
            camera.parallax_offset(0.18),
        )
        if camera.ground_y < self._height + 40:
            self._blit_tiled(
                surface,
                self._near,
                round(camera.ground_y - self._near.get_height() + 10),
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
            ((40.0, 34.0, 7), (52.0, 37.0, 5), (67.0, 31.0, 4))
        ):
            x = camera.screen_x(world_x) + camera.parallax_offset(0.02) * (index + 1) * 0.1
            y = camera.screen_y(altitude)
            if -50 < x < self._width + 50 and -50 < y < self._height:
                pygame.draw.aalines(
                    surface,
                    theme.MOUNTAIN_NEAR,
                    False,
                    [(x - size, y), (x, y - size * 0.55), (x + size, y)],
                )
                pygame.draw.aalines(
                    surface,
                    theme.MOUNTAIN_NEAR,
                    False,
                    [(x + size, y), (x + size * 1.8, y - size * 0.3)],
                )

    def _draw_ground(self, surface: pygame.Surface, camera: Camera) -> None:
        ground_y = camera.ground_y
        if ground_y >= self._height + 40:
            return

        top = round(ground_y)
        surface.blit(self._ground, (0, top))
        pygame.draw.line(
            surface,
            theme.GROUND_LINE,
            (0, top),
            (self._width, top),
            3,
        )

        shift = round(camera.parallax_offset(1.0)) % (self._width + 40)
        for index in range(0, self._width + 40, 14):
            x = (index - shift) % (self._width + 40) - 20
            blade = 4 + (index * 37) % 13
            pygame.draw.line(
                surface,
                theme.GROUND_LINE,
                (x, top),
                (x + blade // 2, top - blade),
                2,
            )
        for index in range(0, self._width + 40, 97):
            x = (index - shift) % (self._width + 40) - 20
            pygame.draw.circle(
                surface,
                theme.MOUNTAIN_NEAR,
                (x, top + 14 + (index * 13) % 24),
                2 + index % 3,
            )
