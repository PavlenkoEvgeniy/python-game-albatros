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

# Parallax factors of the four ridge planes, deepest first. The visible drift
# speed grows monotonically with each nearer plane, which is what makes the
# farthest haze read as genuine distance.
RIDGE_PARALLAX = (0.015, 0.035, 0.18, 0.50)

# Nominal crest heights of the four planes as fractions of the logical height,
# deepest first. Every plane is drawn with extra depth below its nominal band so
# its body always reaches behind the nearer planes and the ground: without it,
# the flat bottom edge of a distant texture shows sky through beneath it and the
# mountains read as floating islands.
RIDGE_HEIGHTS = (0.24, 0.36, 0.30, 0.19)
RIDGE_EXTRA_DEPTH = 0.30

# Distance milestones stand in the grass every 50 metres of world space.
MARKER_SPAN_M = 50.0

GRASS_BAND_BOTTOM = 24


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
    haze: float = 0.0


def _ridge_height(t: float, amplitude: float, phase: float) -> float:
    """Multi-octave ridgeline: integer harmonics keep the tile seamless.

    Sharpening the wave with a fractional power puts narrow crests and wide
    valleys on the skyline, which reads as a real range rather than a sine.
    """
    broad = math.sin(t * math.tau * 2.0 + phase)
    medium = math.sin(t * math.tau * 5.0 + phase * 1.7)
    detail = math.sin(t * math.tau * 11.0 + phase * 2.3)
    wave = broad * 0.58 + medium * 0.30 + detail * 0.12
    crest = math.copysign(abs(wave) ** 1.4, wave)
    return 0.18 + amplitude * (0.52 + 0.48 * crest)


def _make_ridge(
    width: int,
    nominal_height: int,
    extra_depth: int,
    palette: _RidgePalette,
    phase: float,
    amplitude: float,
    seed: int,
) -> pygame.Surface:
    """Draw a tileable mountain layer with volume, lit crests and scree.

    ``extra_depth`` appends solid mountain mass below the nominal band so the
    plane continues behind nearer planes and the ground line.
    """
    height = nominal_height + extra_depth
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    rng = random.Random(seed)

    # Atmospheric perspective: distant planes fade toward a single haze tone.
    haze = theme.clamp01(palette.haze)
    base = theme.lerp_color(palette.base, theme.MOUNTAIN_HAZE, haze)
    light = theme.lerp_color(palette.light, theme.MOUNTAIN_HAZE, haze)
    shadow = theme.lerp_color(palette.shadow, theme.MOUNTAIN_HAZE, haze)
    snow = (
        None if palette.snow is None else theme.lerp_color(palette.snow, theme.MOUNTAIN_HAZE, haze)
    )

    heights: list[int] = []
    for x in range(width):
        crest = nominal_height * _ridge_height(x / max(1, width - 1), amplitude, phase)
        heights.append(max(2, min(height - 1, round(nominal_height - crest))))
    heights[-1] = heights[0]

    # Vertical light falloff: lit rock below the crest dithers into shadow at
    # the foot, which gives the silhouette mass instead of a flat fill. Below
    # the nominal band the gradient clamps to full shadow.
    for x, ridge_y in enumerate(heights):
        depth = max(1, nominal_height - ridge_y)
        for y in range(ridge_y, height):
            t = (y - ridge_y) / depth
            if t < 0.30:
                colour = theme.dither_color(light, base, x, y, t / 0.30)
            else:
                colour = theme.dither_color(base, shadow, x, y, (t - 0.30) / 0.70 * 0.85)
            surface.set_at((x, y), colour)

    # Directional crest lighting: slopes rising toward the sun (on the right)
    # get a lit edge, falling slopes get a dark one.
    for x in range(width):
        previous = heights[(x - 1) % width]
        current = heights[x]
        if current == previous:
            continue
        edge = light if current < previous else shadow
        y = min(current, previous)
        if y < height:
            surface.set_at((x, y), edge)

    # Diagonal scree gullies running down from the crest line.
    streak_count = max(10, width // 24)
    for _ in range(streak_count):
        x = rng.randrange(width)
        top = heights[x] + rng.randrange(4, max(5, min(30, height - heights[x])))
        if top >= height:
            continue
        length = rng.randrange(3, 10)
        colour = shadow if rng.random() < 0.55 else light
        drift = 1 if rng.random() < 0.5 else -1
        for step in range(length):
            px = x + step
            py = top + (step // 3) * drift
            if px < width and py < height:
                surface.set_at((px, py), colour)

    if snow is not None:
        for x in range(width):
            ridge_y = heights[x]
            if ridge_y >= round(nominal_height * 0.34):
                continue
            depth = 2 + (x * 13 + seed) % 4
            for y in range(ridge_y, min(height, ridge_y + depth)):
                snow_line = (y - ridge_y + 1) / depth
                surface.set_at((x, y), theme.dither_color(snow, base, x, y, snow_line))
    return surface


def _make_cloud(width: int, height: int, rng: random.Random) -> pygame.Surface:
    """Sunset-lit cloud: violet tops, warm light dithering in from below."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    puffs = (
        (0.02, 0.40, 0.52, 0.42),
        (0.18, 0.18, 0.48, 0.54),
        (0.44, 0.32, 0.43, 0.42),
        (0.12, 0.54, 0.72, 0.28),
    )
    rects = []
    for left, top, width_ratio, height_ratio in puffs:
        rect = pygame.Rect(
            round(width * left),
            round(height * top),
            max(2, round(width * width_ratio)),
            max(1, round(height * height_ratio)),
        )
        rects.append(rect)
        pygame.draw.rect(surface, theme.CLOUD_SHADE, rect)

    # The sun sits below the clouds, so their undersides catch the warm light:
    # the lower 45% of every puff dithers from violet shade into the lit tone.
    for rect in rects:
        band_top = rect.top + round(rect.height * 0.55)
        band_height = max(1, rect.bottom - band_top)
        for y in range(band_top, rect.bottom):
            amount = (y - band_top + 1) / band_height * 1.2
            for x in range(rect.left, rect.right):
                if surface.get_at((x, y)).a:
                    surface.set_at(
                        (x, y),
                        theme.dither_color(theme.CLOUD_SHADE, theme.CLOUD_LIGHT, x, y, amount),
                    )
        for x in range(rect.left, rect.right):
            if surface.get_at((x, rect.bottom - 1)).a:
                surface.set_at((x, rect.bottom - 1), theme.CLOUD_LIGHT)
    if width > 34 and rng.random() < 0.8:
        highlight = pygame.Rect(
            width // 3,
            round(height * 0.6),
            max(2, width // 4),
            max(1, round(height * 0.3)),
        )
        pygame.draw.rect(surface, theme.CLOUD_LIGHT, highlight)
        for x in range(highlight.left, highlight.right):
            if highlight.top > 0 and surface.get_at((x, highlight.top - 1)).a:
                surface.set_at((x, highlight.top - 1), theme.CLOUD_LIGHT)
    return surface


def _make_sun(radius: int) -> pygame.Surface:
    size = radius * 4
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    pygame.draw.circle(surface, theme.SUN_RING, center, radius)
    pygame.draw.circle(surface, theme.SUN_GLOW, center, max(2, round(radius * 0.72)))
    pygame.draw.circle(surface, theme.SUN_CORE, center, max(2, round(radius * 0.48)))
    return surface


def _make_marker() -> pygame.Surface:
    """A distance milestone: a pylon with a cream pennant, planted in the grass."""
    surface = pygame.Surface((9, 16), pygame.SRCALPHA)
    # pole with a dark right edge so it reads against sky and grass alike
    for y in range(4, 16):
        surface.set_at((2, y), theme.TEXT)
        surface.set_at((3, y), theme.TEXT_SHADOW)
    # right-pointing pennant with an accent tip
    for row in range(5):
        for x in range(6 - row):
            surface.set_at((2 + x, row), theme.TEXT)
    surface.set_at((7, 0), theme.ACCENT)
    surface.set_at((6, 1), theme.ACCENT)
    return surface


def _make_ground_tile(width: int, height: int, seed: int) -> pygame.Surface:
    """Grass-covered ground: blades above the ground line, soil beneath.

    Every per-column pattern repeats with a period that divides the tile width,
    otherwise the tuft edge would show a seam every ``width`` pixels.
    """
    rng = random.Random(seed)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    band_bottom = min(GRASS_BAND_BOTTOM, height - 1)
    for x in range(width):
        tuft = 2 + (x * 5 + seed) % 4
        # Sparse blade tips poke above the ground line; gaps stay transparent
        # so the mountains show through behind the tuft.
        if (x * 3 + seed) % 4 != 3:
            blade = theme.GROUND_LINE if (x + seed) % 2 else theme.GROUND_LIGHT
            pygame.draw.rect(surface, blade, (x, 0, 1, tuft))
        pygame.draw.rect(surface, theme.GROUND_TOP, (x, tuft, 1, band_bottom - tuft))
        pygame.draw.rect(surface, theme.GROUND_LIGHT, (x, tuft, 1, 2))
        if (x * 11 + seed) % 8 == 0:
            stroke = 3 + (x // 8 + seed) % 2
            pygame.draw.rect(surface, theme.GROUND_LINE, (x, max(0, tuft - 2), 1, stroke))
        if (x * 7 + seed) % 16 == 0:
            pygame.draw.rect(surface, theme.GRASS_DEEP, (x, tuft + 3, 1, 5))
        if (x * 5 + seed) % 12 == 0:
            surface.set_at((x, min(band_bottom - 7, tuft + 3)), theme.GROUND_LIGHT)
        for y in range(band_bottom - 6, band_bottom):
            depth = (y - band_bottom + 6) / 6
            surface.set_at(
                (x, y),
                theme.dither_color(theme.GROUND_TOP, theme.GRASS_DEEP, x, y, depth),
            )

    # A few flowers on the tuft line; a flower always grows its own blade.
    for flower_x, colour in (
        ((13 + seed * 3) % width, theme.ACCENT),
        ((37 + seed * 5) % width, theme.TEXT),
    ):
        tuft = 2 + (flower_x * 5 + seed) % 4
        if (flower_x * 3 + seed) % 4 == 3:
            pygame.draw.rect(surface, theme.GROUND_LIGHT, (flower_x, 0, 1, tuft))
        surface.set_at((flower_x, max(0, tuft - 1)), colour)
        surface.set_at((flower_x, min(band_bottom - 1, tuft)), theme.GROUND_LIGHT)

    # Soil under the grass with stones, roots and dithered shading rows.
    pygame.draw.rect(surface, theme.GROUND_BOTTOM, (0, band_bottom, width, height - band_bottom))
    for x in range(width):
        for y in (band_bottom, band_bottom + 1):
            depth = 0.35 if y == band_bottom else 0.15
            surface.set_at(
                (x, y),
                theme.dither_color(theme.GROUND_BOTTOM, theme.GRASS_DEEP, x, y, depth),
            )
    for y in range(band_bottom + 4, height, 7):
        pygame.draw.rect(surface, theme.GROUND_DARK, (0, y, width, 2))
    for _ in range(max(6, width // 5)):
        x = rng.randrange(width)
        y = rng.randrange(band_bottom + 2, max(band_bottom + 3, height - 4))
        length = rng.randrange(2, 5)
        colour = theme.GROUND_STONE if rng.random() < 0.6 else theme.GROUND_DARK
        pygame.draw.rect(surface, colour, (x, y, length, 2))
    for _ in range(max(3, width // 10)):
        x = rng.randrange(width)
        pygame.draw.rect(surface, theme.GROUND_DARK, (x, band_bottom + 1, 1, rng.randrange(2, 5)))
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

        self._sun = _make_sun(max(5, round(self._height * 0.065)))
        self._sun_position = (round(self._width * 0.81), round(self._height * 0.16))
        self._bake_sun_glow(round(self._height * 0.22))

        self._far_width = self._width * 2
        extra_depth = round(self._height * RIDGE_EXTRA_DEPTH)
        # Four ridge planes with atmospheric perspective: the faintest haze
        # plane sits deepest, each nearer plane is taller, darker and faster.
        self._haze = _make_ridge(
            self._far_width,
            round(self._height * RIDGE_HEIGHTS[0]),
            extra_depth,
            _RidgePalette(
                theme.MOUNTAIN_FAR,
                theme.MOUNTAIN_FAR_LIGHT,
                theme.MOUNTAIN_SHADOW,
                theme.MOUNTAIN_SNOW,
                haze=0.72,
            ),
            phase=5.5,
            amplitude=0.62,
            seed=seed + 5,
        )
        self._far = _make_ridge(
            self._far_width,
            round(self._height * RIDGE_HEIGHTS[1]),
            extra_depth,
            _RidgePalette(
                theme.MOUNTAIN_FAR,
                theme.MOUNTAIN_FAR_LIGHT,
                theme.MOUNTAIN_SHADOW,
                theme.MOUNTAIN_SNOW,
                haze=0.45,
            ),
            phase=0.4,
            amplitude=0.75,
            seed=seed + 1,
        )
        self._mid_width = self._width * 2
        self._mid = _make_ridge(
            self._mid_width,
            round(self._height * RIDGE_HEIGHTS[2]),
            extra_depth,
            _RidgePalette(
                theme.MOUNTAIN_MID,
                theme.MOUNTAIN_MID_LIGHT,
                theme.MOUNTAIN_SHADOW,
                haze=0.18,
            ),
            phase=2.1,
            amplitude=0.9,
            seed=seed + 2,
        )
        self._near_width = self._width * 2
        self._near = _make_ridge(
            self._near_width,
            round(self._height * RIDGE_HEIGHTS[3]),
            extra_depth,
            _RidgePalette(
                theme.MOUNTAIN_NEAR,
                theme.MOUNTAIN_NEAR_LIGHT,
                theme.GROUND_DARK,
            ),
            phase=4.6,
            amplitude=0.85,
            seed=seed + 3,
        )
        self._cloud_span_m = 170.0
        self._clouds = self._make_clouds()
        self._ground_tile = _make_ground_tile(64, self._height + 64, seed + 4)
        self._marker = _make_marker()

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

    def _bake_sun_glow(self, radius: int) -> None:
        """Dither a soft halo around the sun into the static sky.

        Each affected pixel dithers from its own band colour toward the sun's
        glow colour with a radial falloff, so the frame keeps a limited palette
        while the sun reads as a bright modern bloom.
        """
        if radius <= 0:
            return
        cx, cy = self._sun_position
        x0 = max(0, round(cx - radius))
        x1 = min(self._width - 1, round(cx + radius))
        y0 = max(0, round(cy - radius))
        y1 = min(self._height - 1, round(cy + radius))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                distance = math.hypot(x - cx, y - cy) / radius
                if distance >= 1.0:
                    continue
                amount = (1.0 - distance) ** 1.6 * 0.85
                colour = self._sky.get_at((x, y))
                current = (colour.r, colour.g, colour.b)
                self._sky.set_at(
                    (x, y),
                    theme.dither_color(current, theme.SUN_GLOW, x, y, amount),
                )

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
        haze_height = round(self._height * RIDGE_HEIGHTS[0])
        haze_y = horizon - haze_height + round(self._height * 0.055)
        self._blit_tiled(surface, self._haze, haze_y, camera.parallax_offset(RIDGE_PARALLAX[0]))

        far_height = round(self._height * RIDGE_HEIGHTS[1])
        far_y = horizon - far_height + round(self._height * 0.045)
        self._blit_tiled(surface, self._far, far_y, camera.parallax_offset(RIDGE_PARALLAX[1]))

        mid_height = round(self._height * RIDGE_HEIGHTS[2])
        near_height = round(self._height * RIDGE_HEIGHTS[3])
        mid_base = min(camera.ground_y, self._height * 0.94) + 9
        self._blit_tiled(
            surface,
            self._mid,
            round(mid_base - mid_height),
            camera.parallax_offset(RIDGE_PARALLAX[2]),
        )
        if camera.ground_y < self._height + 20:
            self._blit_tiled(
                surface,
                self._near,
                round(camera.ground_y - near_height + 5),
                camera.parallax_offset(RIDGE_PARALLAX[3]),
            )

        self._draw_distant_birds(surface, camera)
        self._draw_ground(surface, camera)
        self._draw_markers(surface, camera)

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

    def _draw_markers(self, surface: pygame.Surface, camera: Camera) -> None:
        """Plant a milestone every MARKER_SPAN_M metres, scrolling with the ground."""
        if camera.ground_y >= self._height + 8:
            return
        ground_y = round(camera.ground_y)
        marker_height = self._marker.get_height()
        left_margin_m = 8.0 / camera.pixels_per_meter
        first = math.floor((camera.x_m - left_margin_m) / MARKER_SPAN_M) * MARKER_SPAN_M
        index = 0
        while True:
            world_x = first + index * MARKER_SPAN_M
            x = camera.screen_x(world_x)
            if x > self._width + 8:
                break
            if x >= -8:
                surface.blit(self._marker, (round(x), ground_y - marker_height + 2))
            index += 1
