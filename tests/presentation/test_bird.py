from __future__ import annotations

import pygame

from albatross.presentation.bird import FLAP_DURATION_S, Bird


def test_gliding_keeps_wings_in_a_single_spread_pose() -> None:
    bird = Bird()
    poses = set()
    for _ in range(120):
        assert 0.0 <= bird.wing_lift <= 0.1  # spread pose, no twitching
        poses.add(pygame.image.tobytes(bird._sprite_for(bird.wing_lift, 0.0), "RGBA"))
        bird.update(0.016)

    assert len(poses) == 1  # the glide never switches sprite phases


def test_flap_animation_runs_and_finishes() -> None:
    bird = Bird()
    bird.notify_flap()
    assert bird.flapping is True

    lifts: list[float] = []
    for _ in range(40):
        lifts.append(bird.wing_lift)
        bird.update(FLAP_DURATION_S / 20)

    assert max(lifts) > 0.5  # a strong downstroke
    assert min(lifts) < -0.5  # and a full upstroke before settling back
    assert bird.flapping is False
    assert 0.0 <= bird.wing_lift <= 0.1


def test_update_ignores_negative_time() -> None:
    bird = Bird()
    bird.notify_flap()
    bird.update(-1.0)
    assert bird.flapping is True


def test_draw_produces_visible_pixels() -> None:
    bird = Bird()
    surface = pygame.Surface((400, 300), pygame.SRCALPHA)

    bird.draw(surface, (200, 150), vertical_speed=0.0)

    bounds = surface.get_bounding_rect(min_alpha=1)
    assert bounds.width > 0
    assert bounds.height > 0


def test_draw_handles_extreme_vertical_speeds() -> None:
    bird = Bird()
    surface = pygame.Surface((400, 300), pygame.SRCALPHA)
    bird.draw(surface, (200, 150), vertical_speed=-100.0)
    bird.draw(surface, (200, 150), vertical_speed=100.0)
    assert surface.get_bounding_rect(min_alpha=1).width > 0


def test_wing_phases_produce_distinct_non_empty_sprites() -> None:
    bird = Bird()

    sprites = [bird._sprite_for(lift, 0.0) for lift in (-0.9, 0.0, 0.45, 0.9)]
    payloads = {pygame.image.tobytes(sprite, "RGBA") for sprite in sprites}

    assert len(payloads) == len(sprites)
    assert all(sprite.get_bounding_rect(min_alpha=1).width > 8 for sprite in sprites)


def test_sprite_keeps_clear_of_its_edges_in_every_pose() -> None:
    bird = Bird()
    speeds = (-100.0, -2.0, 0.0, 2.0, 100.0)

    for lift in (-0.9, 0.0, 0.45, 0.9):
        for speed in speeds:
            sprite = bird._sprite_for(lift, speed)
            width, height = sprite.get_size()
            edge_pixels = (
                [(x, 0) for x in range(width)]
                + [(x, height - 1) for x in range(width)]
                + [(0, y) for y in range(height)]
                + [(width - 1, y) for y in range(height)]
            )
            assert all(sprite.get_at(pixel).a == 0 for pixel in edge_pixels), (lift, speed)


def test_sprite_footprint_is_smaller_than_the_previous_design() -> None:
    bird = Bird()

    for lift in (-0.9, 0.0, 0.45, 0.9):
        sprite = bird._sprite_for(lift, 0.0)
        bounds = sprite.get_bounding_rect(min_alpha=1)

        assert bounds.width <= 34
        assert bounds.height <= 20


def test_pitch_poses_are_distinct_and_cached() -> None:
    bird = Bird()

    climbing = bird._sprite_for(0.0, -20.0)
    level = bird._sprite_for(0.0, 0.0)
    diving = bird._sprite_for(0.0, 20.0)

    assert pygame.image.tobytes(climbing, "RGBA") != pygame.image.tobytes(level, "RGBA")
    assert pygame.image.tobytes(diving, "RGBA") != pygame.image.tobytes(level, "RGBA")
    assert bird._sprite_for(0.0, 20.0) is diving
