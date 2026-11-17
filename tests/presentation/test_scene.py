from __future__ import annotations

import pygame
import pytest

from albatross.presentation.camera import Camera
from albatross.presentation.scene import Scene


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
