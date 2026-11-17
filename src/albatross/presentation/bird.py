"""Procedural albatross silhouette and wing animation."""

from __future__ import annotations

import math

import pygame

from albatross.presentation import theme

FLAP_DURATION_S = 0.32
SUPERSAMPLE = 2
DRAW_SIZE = (250, 170)


class Bird:
    """Animation state for the player's bird."""

    def __init__(self) -> None:
        self._flap_timer = 0.0
        self._time = 0.0

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
        """Draw the bird, pitching slightly with vertical speed."""
        highres = self._draw_highres(self.wing_lift)
        pitch = max(-12.0, min(12.0, -vertical_speed * 0.9))
        rotated = pygame.transform.rotozoom(highres, pitch, 1.0)
        scaled = pygame.transform.smoothscale(rotated, DRAW_SIZE)
        rect = scaled.get_rect(center=center)
        surface.blit(scaled, rect)

    def _draw_highres(self, wing_lift: float) -> pygame.Surface:
        size = (DRAW_SIZE[0] * SUPERSAMPLE, DRAW_SIZE[1] * SUPERSAMPLE)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        cx, cy = size[0] // 2, size[1] // 2

        def point(x: float, y: float) -> tuple[int, int]:
            return (round(cx + x * SUPERSAMPLE), round(cy + y * SUPERSAMPLE))

        tail = [point(-58, 1), point(-88, -15), point(-80, 13)]
        pygame.draw.polygon(surface, theme.BIRD_SHADE, tail)

        far_wing = [
            point(-20, -8),
            point(-48, -12 + wing_lift * 18),
            point(-82, -4 + wing_lift * 38),
            point(-52, 6 + wing_lift * 10),
            point(-24, 3),
        ]
        pygame.draw.polygon(surface, theme.BIRD_SHADE, far_wing)
        pygame.draw.aalines(surface, theme.BIRD_WINGTIP, True, far_wing)

        body = [
            point(-64, 1),
            point(-54, -12),
            point(-10, -17),
            point(32, -10),
            point(50, -2),
            point(32, 8),
            point(-12, 13),
            point(-52, 10),
        ]
        pygame.draw.polygon(surface, theme.BIRD_BODY, body)
        pygame.draw.aalines(surface, theme.BIRD_WINGTIP, True, body)

        pygame.draw.circle(surface, theme.BIRD_BODY, point(55, -4), 13 * SUPERSAMPLE)
        pygame.draw.aacircle(surface, theme.BIRD_WINGTIP, point(55, -4), 13 * SUPERSAMPLE)
        pygame.draw.circle(surface, theme.BIRD_EYE, point(60, -8), 2 * SUPERSAMPLE)

        beak = [point(67, -5), point(86, 0), point(67, 5)]
        pygame.draw.polygon(surface, theme.BIRD_BEAK, beak)

        near_wing = [
            point(-18, -12),
            point(-46, -14 + wing_lift * 18),
            point(-84, -6 + wing_lift * 42),
            point(-54, 8 + wing_lift * 12),
            point(-22, 8),
        ]
        pygame.draw.polygon(surface, theme.BIRD_BODY, near_wing)
        pygame.draw.aalines(surface, theme.BIRD_WINGTIP, True, near_wing)
        tip = [
            point(-84, -6 + wing_lift * 42),
            point(-66, -2 + wing_lift * 30),
            point(-70, 4 + wing_lift * 18),
        ]
        pygame.draw.polygon(surface, theme.BIRD_WINGTIP, tip)

        pygame.draw.aaline(
            surface,
            theme.BIRD_WINGTIP,
            point(-58, 6),
            point(36, 5),
        )
        return surface
