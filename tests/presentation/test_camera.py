from __future__ import annotations

import pytest

from albatross.presentation.camera import Camera


def make_camera() -> Camera:
    return Camera(width=800, height=400, pixels_per_meter=8.0)


def test_first_follow_frames_the_bird_at_the_anchor() -> None:
    camera = make_camera()
    camera.follow(world_x_m=100.0, altitude_m=50.0, dt=0.0)

    assert camera.initialized is True
    assert camera.screen_x(100.0) == pytest.approx(800 * camera.anchor_x_ratio)
    assert camera.screen_y(50.0) == pytest.approx(400 * 0.40)


def test_horizontal_tracking_is_exact() -> None:
    camera = make_camera()
    camera.follow(0.0, 50.0, 0.0)
    camera.follow(25.0, 50.0, 1 / 60)

    assert camera.screen_x(25.0) == pytest.approx(800 * camera.anchor_x_ratio)


def test_vertical_follow_is_smoothed() -> None:
    camera = make_camera()
    camera.follow(0.0, 50.0, 0.0)
    target = camera.target_altitude(100.0)
    start = camera.altitude_m

    camera.follow(0.0, 100.0, 1 / 60)

    assert start < camera.altitude_m < target
    assert camera.screen_y(100.0) < 400 * 0.40

    for _ in range(300):
        camera.follow(0.0, 100.0, 1 / 60)
    assert camera.altitude_m == pytest.approx(target)
    assert camera.screen_y(100.0) == pytest.approx(400 * 0.40)


def test_zero_dt_keeps_the_vertical_position() -> None:
    camera = make_camera()
    camera.follow(0.0, 100.0, 0.0)
    altitude = camera.altitude_m

    camera.follow(30.0, 10.0, 0.0)

    assert camera.altitude_m == altitude
    assert camera.screen_x(30.0) == pytest.approx(800 * camera.anchor_x_ratio)


def test_camera_never_goes_below_ground() -> None:
    camera = make_camera()
    camera.follow(0.0, 0.0, 0.0)

    assert camera.altitude_m == 0.0
    assert camera.ground_y == pytest.approx(200.0)


def test_parallax_scales_with_depth() -> None:
    camera = make_camera()
    camera.follow(50.0, 50.0, 0.0)

    assert camera.parallax_offset(1.0) > camera.parallax_offset(0.2) > 0
    assert camera.parallax_offset(0.0) == 0.0


def test_ground_moves_down_when_the_bird_climbs() -> None:
    camera = make_camera()
    camera.follow(0.0, 30.0, 0.0)
    low_ground = camera.ground_y

    camera.follow(0.0, 80.0, 10.0)

    assert camera.ground_y > low_ground
