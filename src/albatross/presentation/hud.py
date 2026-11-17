"""Heads-up display and full-screen overlays."""

from __future__ import annotations

import math

import pygame

from albatross.domain.config import FlightConfig
from albatross.domain.session import GamePhase, SessionState
from albatross.presentation import theme
from albatross.presentation.fonts import render_text
from albatross.presentation.i18n import TextKey, Translator

Anchor = tuple[str, tuple[int, int]]


def _draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: theme.RGB,
    anchor: Anchor,
    shadow: bool = True,
) -> pygame.Rect:
    image = render_text(text, size, color)
    rect = image.get_rect()
    match anchor[0]:
        case "topleft":
            rect.topleft = anchor[1]
        case "topright":
            rect.topright = anchor[1]
        case "bottomleft":
            rect.bottomleft = anchor[1]
        case "bottomright":
            rect.bottomright = anchor[1]
        case _:
            rect.center = anchor[1]
    if shadow:
        shadow_image = render_text(text, size, theme.TEXT_SHADOW)
        surface.blit(shadow_image, rect.move(2, 2))
    surface.blit(image, rect)
    return rect


class Hud:
    """Draws the HUD for every game phase."""

    def __init__(self, config: FlightConfig, size: tuple[int, int]) -> None:
        self._config = config
        self._width, self._height = size

    def draw(
        self,
        surface: pygame.Surface,
        state: SessionState,
        translator: Translator,
        muted: bool,
        elapsed_s: float,
    ) -> None:
        if state.phase is GamePhase.MENU:
            self._draw_menu(surface, state, translator, muted, elapsed_s)
            return

        self._draw_playing(surface, state, translator, muted)
        if state.phase is GamePhase.PAUSED:
            self._draw_pause(surface, translator)
        elif state.phase is GamePhase.GAME_OVER:
            self._draw_game_over(surface, state, translator)

    def _draw_playing(
        self,
        surface: pygame.Surface,
        state: SessionState,
        translator: Translator,
        muted: bool,
    ) -> None:
        self._draw_stamina(surface, state, translator)
        self._draw_distance(surface, state, translator)
        _draw_text(
            surface,
            translator.text(TextKey.PLAY_HINT),
            18,
            theme.TEXT_MUTED,
            ("bottomleft", (40, self._height - 30)),
        )
        _draw_text(
            surface,
            translator.text(TextKey.SOUND_OFF if muted else TextKey.SOUND_ON),
            18,
            theme.TEXT_MUTED,
            ("bottomright", (self._width - 40, self._height - 30)),
        )

    def _draw_stamina(
        self,
        surface: pygame.Surface,
        state: SessionState,
        translator: Translator,
    ) -> None:
        fraction = theme.clamp01(state.flight.stamina / self._config.stamina_max)
        label_rect = _draw_text(
            surface,
            translator.text(TextKey.STAMINA_LABEL),
            20,
            theme.TEXT_MUTED,
            ("topleft", (42, 34)),
        )
        bar = pygame.Rect(42, label_rect.bottom + 6, 300, 18)
        theme.rounded_rect(surface, bar, theme.STAMINA_TRACK, radius=9)
        fill_width = round((bar.width - 4) * fraction)
        if fill_width > 0:
            fill = pygame.Rect(bar.x + 2, bar.y + 2, fill_width, bar.height - 4)
            color = theme.STAMINA_LOW if fraction < 0.25 else theme.STAMINA_FILL
            theme.rounded_rect(surface, fill, color, radius=7)
        theme.rounded_rect(surface, bar, theme.STAMINA_BORDER, radius=9, width=1)

    def _draw_distance(
        self,
        surface: pygame.Surface,
        state: SessionState,
        translator: Translator,
    ) -> None:
        _draw_text(
            surface,
            translator.text(TextKey.DISTANCE_LABEL),
            20,
            theme.TEXT_MUTED,
            ("topright", (self._width - 44, 34)),
        )
        value = f"{state.flight.distance_m} {translator.text(TextKey.UNIT_M)}"
        _draw_text(
            surface,
            value,
            46,
            theme.TEXT,
            ("topright", (self._width - 44, 60)),
        )
        best = self._record_value(state.best_distance_m, translator)
        _draw_text(
            surface,
            f"{translator.text(TextKey.BEST_LABEL)}: {best}",
            20,
            theme.TEXT_MUTED,
            ("topright", (self._width - 44, 118)),
        )

    def _draw_menu(
        self,
        surface: pygame.Surface,
        state: SessionState,
        translator: Translator,
        muted: bool,
        elapsed_s: float,
    ) -> None:
        overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((6, 10, 18, 48))
        surface.blit(overlay, (0, 0))

        _draw_text(
            surface,
            translator.text(TextKey.TITLE),
            112,
            theme.TEXT,
            ("center", (self._width // 2, round(self._height * 0.26))),
        )
        _draw_text(
            surface,
            translator.text(TextKey.SUBTITLE),
            30,
            theme.ACCENT,
            ("center", (self._width // 2, round(self._height * 0.36))),
        )
        best = self._record_value(state.best_distance_m, translator)
        _draw_text(
            surface,
            f"{translator.text(TextKey.BEST_LABEL)}: {best}",
            24,
            theme.TEXT_MUTED,
            ("center", (self._width // 2, round(self._height * 0.48))),
        )

        pulse = 0.5 + 0.5 * math.sin(elapsed_s * 2.4)
        hint = render_text(translator.text(TextKey.START_HINT), 30, theme.TEXT)
        hint.set_alpha(round(170 + 85 * pulse))
        hint_rect = hint.get_rect(center=(self._width // 2, round(self._height * 0.62)))
        surface.blit(hint, hint_rect)

        _draw_text(
            surface,
            translator.text(TextKey.MENU_CONTROLS),
            19,
            theme.TEXT_MUTED,
            ("center", (self._width // 2, self._height - 72)),
        )
        _draw_text(
            surface,
            translator.text(TextKey.SOUND_OFF if muted else TextKey.SOUND_ON),
            18,
            theme.TEXT_MUTED,
            ("bottomright", (self._width - 40, self._height - 34)),
        )

    def _draw_pause(self, surface: pygame.Surface, translator: Translator) -> None:
        self._overlay(surface)
        panel = pygame.Rect(0, 0, 520, 210)
        panel.center = (self._width // 2, self._height // 2)
        theme.rounded_rect(surface, panel, theme.PANEL, radius=24)
        theme.rounded_rect(surface, panel, theme.PANEL_BORDER, radius=24, width=1)
        _draw_text(
            surface,
            translator.text(TextKey.PAUSED),
            54,
            theme.TEXT,
            ("center", (self._width // 2, panel.centery - 38)),
        )
        _draw_text(
            surface,
            translator.text(TextKey.PAUSE_HINT),
            24,
            theme.TEXT_MUTED,
            ("center", (self._width // 2, panel.centery + 42)),
        )

    def _draw_game_over(
        self,
        surface: pygame.Surface,
        state: SessionState,
        translator: Translator,
    ) -> None:
        self._overlay(surface)
        panel = pygame.Rect(0, 0, 640, 350)
        panel.center = (self._width // 2, self._height // 2)
        theme.rounded_rect(surface, panel, theme.PANEL, radius=24)
        theme.rounded_rect(surface, panel, theme.PANEL_BORDER, radius=24, width=1)

        _draw_text(
            surface,
            translator.text(TextKey.GAME_OVER_TITLE),
            48,
            theme.TEXT,
            ("center", (panel.centerx, panel.top + 54)),
        )
        _draw_text(
            surface,
            translator.text(TextKey.GAME_OVER_SUBTITLE),
            22,
            theme.TEXT_MUTED,
            ("center", (panel.centerx, panel.top + 96)),
        )

        distance = state.last_distance_m if state.last_distance_m is not None else 0
        _draw_text(
            surface,
            f"{translator.text(TextKey.DISTANCE_LABEL)}: "
            f"{distance} {translator.text(TextKey.UNIT_M)}",
            38,
            theme.TEXT,
            ("center", (panel.centerx, panel.top + 162)),
        )
        best = self._record_value(state.best_distance_m, translator)
        _draw_text(
            surface,
            f"{translator.text(TextKey.BEST_LABEL)}: {best}",
            24,
            theme.TEXT_MUTED,
            ("center", (panel.centerx, panel.top + 208)),
        )
        if state.new_record:
            _draw_text(
                surface,
                translator.text(TextKey.NEW_RECORD),
                26,
                theme.NEW_RECORD,
                ("center", (panel.centerx, panel.top + 248)),
            )
        _draw_text(
            surface,
            translator.text(TextKey.RESTART_HINT),
            22,
            theme.TEXT,
            ("center", (panel.centerx, panel.bottom - 42)),
        )

    def _overlay(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((6, 10, 18, 150))
        surface.blit(overlay, (0, 0))

    @staticmethod
    def _record_value(best: int | None, translator: Translator) -> str:
        if best is None:
            return translator.text(TextKey.BEST_EMPTY)
        return f"{best} {translator.text(TextKey.UNIT_M)}"
