"""Composes scene, bird and HUD into one frame."""

from __future__ import annotations

import pygame

from albatross.domain.config import FlightConfig
from albatross.domain.session import GamePhase, SessionState
from albatross.presentation import theme
from albatross.presentation.bird import Bird
from albatross.presentation.camera import Camera
from albatross.presentation.hud import Hud
from albatross.presentation.i18n import Translator
from albatross.presentation.scene import Scene

STREAK_DURATION_S = 0.45


class Renderer:
    """Owns animation-only state; the simulation is never mutated here."""

    def __init__(self, size: tuple[int, int], config: FlightConfig, seed: int = 7) -> None:
        self._size = size
        self._surface = pygame.Surface(size)
        self._camera = Camera(
            width=size[0],
            height=size[1],
            pixels_per_meter=config.meters_to_pixels,
        )
        self._scene = Scene(size, seed=seed)
        self._bird = Bird()
        self._hud = Hud(config, size)
        self._elapsed_s = 0.0
        self._streak_timer_s = 0.0

    @property
    def surface(self) -> pygame.Surface:
        return self._surface

    def notify_flap(self) -> None:
        self._bird.notify_flap()
        self._streak_timer_s = STREAK_DURATION_S

    def render(
        self,
        state: SessionState,
        dt: float,
        translator: Translator,
        muted: bool,
    ) -> pygame.Surface:
        safe_dt = max(0.0, dt)
        self._elapsed_s += safe_dt
        self._bird.update(safe_dt)
        self._streak_timer_s = max(0.0, self._streak_timer_s - safe_dt)

        camera_dt = safe_dt if state.phase is GamePhase.PLAYING else 0.0
        self._camera.follow(state.flight.x_m, state.flight.altitude_m, camera_dt)

        self._scene.draw(self._surface, self._camera)
        center = (
            round(self._camera.screen_x(state.flight.x_m)),
            round(self._camera.screen_y(state.flight.altitude_m)),
        )
        if self._streak_timer_s > 0.0 and state.phase is GamePhase.PLAYING:
            self._draw_streaks(center)
        self._bird.draw(self._surface, center, state.flight.vertical_speed_mps)
        self._hud.draw(
            self._surface,
            state,
            translator,
            muted,
            self._elapsed_s,
        )
        return self._surface

    def _draw_streaks(self, center: tuple[int, int]) -> None:
        strength = self._streak_timer_s / STREAK_DURATION_S
        for index in range(4):
            length = round((38 + index * 14) * strength)
            if length <= 0:
                continue
            x = center[0] - 52 - index * 9
            y = center[1] - 14 + index * 9
            pygame.draw.line(
                self._surface,
                theme.lerp_color(theme.SKY_HORIZON, theme.TEXT, 0.55),
                (x - length, y),
                (x, y),
                1,
            )
