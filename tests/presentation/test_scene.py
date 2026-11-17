from __future__ import annotations

from itertools import pairwise

import pygame
import pytest

from albatross.presentation import theme
from albatross.presentation.camera import Camera
from albatross.presentation.scene import RIDGE_PARALLAX, Scene


def make_scene_and_camera() -> tuple[Scene, Camera, pygame.Surface]:
    size = (320, 180)
    scene = Scene(size)
    camera = Camera(width=size[0], height=size[1], pixels_per_meter=8.0)
    camera.follow(0.0, 50.0, 0.0)
    return scene, camera, pygame.Surface(size)


def test_scene_draws_a_varied_image() -> None:
    scene, camera, surface = make_scene_and_camera()

    scene.draw(surface, camera)

    colours = {surface.get_at((x, y))[:3] for x in range(0, 320, 8) for y in range(0, 180, 6)}
    assert len(colours) > 4


def test_scene_is_deterministic_for_the_same_seed() -> None:
    left, camera, left_surface = make_scene_and_camera()
    right = Scene((320, 180))
    right_surface = pygame.Surface((320, 180))

    left.draw(left_surface, camera)
    right.draw(right_surface, camera)

    assert pygame.image.tobytes(left_surface, "RGB") == pygame.image.tobytes(
        right_surface,
        "RGB",
    )


def test_scene_handles_high_altitude_where_ground_is_hidden() -> None:
    scene, camera, surface = make_scene_and_camera()
    camera.follow(0.0, 2_000.0, 10.0)

    scene.draw(surface, camera)

    assert camera.ground_y > 180
    sampled = {surface.get_at((x, y))[:3] for x in range(0, 320, 16) for y in range(0, 180, 12)}
    assert len(sampled) > 2


def test_scene_never_loads_external_images(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_load(*args: object, **kwargs: object) -> pygame.Surface:
        raise AssertionError("the scene must stay asset-free")

    monkeypatch.setattr(pygame.image, "load", fail_load)
    monkeypatch.setattr(pygame.image, "load_extended", fail_load)
    scene, camera, surface = make_scene_and_camera()

    scene.draw(surface, camera)

    assert surface.get_bounding_rect(min_alpha=1).size == (320, 180)


def test_mountain_tiles_have_matching_outer_edges() -> None:
    scene = Scene((320, 180))

    for layer in (scene._far, scene._mid, scene._near):
        tops = []
        for x in (0, layer.get_width() - 1):
            for y in range(layer.get_height()):
                if layer.get_at((x, y)).a:
                    tops.append(y)
                    break
        assert abs(tops[0] - tops[1]) <= 1


def test_long_scroll_keeps_every_layer_covered() -> None:
    scene, camera, surface = make_scene_and_camera()

    for world_x in (0.0, 1_000.0, 50_000.0):
        camera.follow(world_x, 50.0, 0.0)
        scene.draw(surface, camera)
        assert surface.get_at((160, 175)).a == 255


def _plane_luminance_stats(surface: pygame.Surface) -> tuple[float, float]:
    """Mean and spread of pixel luminance over the plane's opaque pixels."""
    luminance: list[float] = []
    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            r, g, b, a = surface.get_at((x, y))
            if a:
                luminance.append(0.299 * r + 0.587 * g + 0.114 * b)
    mean = sum(luminance) / len(luminance)
    spread = sum((value - mean) ** 2 for value in luminance) / len(luminance)
    return mean, spread**0.5


def test_scene_has_four_mountain_planes_with_monotonic_parallax() -> None:
    assert len(RIDGE_PARALLAX) == 4
    assert all(left < right for left, right in pairwise(RIDGE_PARALLAX))
    assert RIDGE_PARALLAX[-1] < 1.0  # the ground layer still drifts fastest


def test_farthest_plane_is_paler_and_lower_contrast_than_the_near_one() -> None:
    scene = Scene((320, 180))

    haze_mean, haze_spread = _plane_luminance_stats(scene._haze)
    near_mean, near_spread = _plane_luminance_stats(scene._near)

    assert haze_mean > near_mean
    assert haze_spread < near_spread


def test_mountains_reach_the_ground_without_sky_gaps() -> None:
    """Below the far plane's bottom edge only mountains and ground may show.

    A distant plane's texture ends in a flat bottom edge; if the nearer planes
    leave sky visible under it, the mountains read as floating islands.
    """
    scene, camera, surface = make_scene_and_camera()
    camera.follow(0.0, 10.0, 10.0)  # a large dt lets the camera snap to target altitude
    scene.draw(surface, camera)

    sky = set(theme.SKY_BANDS) | {theme.SUN_GLOW, theme.SUN_CORE, theme.SUN_RING, theme.SKY_HORIZON}
    far_bottom = round(180 * 0.72) + round(180 * 0.045)
    for y in range(far_bottom + 1, min(180, int(camera.ground_y))):
        for x in range(0, 320, 4):
            assert tuple(surface.get_at((x, y))[:3]) not in sky, (x, y)


def test_distance_markers_stand_every_50_metres() -> None:
    size = (320, 180)
    scene = Scene(size)
    camera = Camera(width=size[0], height=size[1], pixels_per_meter=2.0)
    camera.follow(100.0, 6.0, 10.0)  # ground in view, three markers on screen
    surface = pygame.Surface(size)
    scene.draw(surface, camera)

    ground_y = round(camera.ground_y)

    def marker_pixel_near(x: int) -> bool:
        return any(
            tuple(surface.get_at((x + dx, ground_y - 8))[:3]) == theme.TEXT for dx in range(0, 8)
        )

    for world_x in (100.0, 150.0, 200.0):
        x = round(camera.screen_x(world_x))
        assert marker_pixel_near(x), world_x
    # halfway between markers the sky/grass shows, no pole
    for world_x in (125.0, 175.0):
        x = round(camera.screen_x(world_x))
        assert not marker_pixel_near(x), world_x


def test_ground_is_covered_with_grass() -> None:
    scene, camera, surface = make_scene_and_camera()
    camera.follow(0.0, 4.0, 10.0)  # a large dt lets the camera snap to target altitude
    scene.draw(surface, camera)

    tile = scene._ground_tile
    tuft_alphas = {tile.get_at((x, 1)).a for x in range(tile.get_width())}
    assert 0 in tuft_alphas  # gaps between blades let the ridges show through
    assert any(alpha == 255 for alpha in tuft_alphas)

    ground_y = round(camera.ground_y)
    band_colours = {tuple(surface.get_at((x, ground_y + 6))[:3]) for x in range(0, 320, 2)}
    grass = (theme.GROUND_TOP, theme.GROUND_LIGHT, theme.GROUND_LINE, theme.GRASS_DEEP)
    assert any(colour in grass for colour in band_colours)

    tile_colours = {
        tuple(tile.get_at((x, y))[:3])
        for x in range(tile.get_width())
        for y in range(8)
        if tile.get_at((x, y)).a
    }
    assert theme.ACCENT in tile_colours  # flowers grow on the tuft line
    assert theme.TEXT in tile_colours
