from __future__ import annotations

import pygame

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
