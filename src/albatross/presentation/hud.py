"""Heads-up display and full-screen overlays."""

from __future__ import annotations

import math

import pygame

from albatross.domain.config import FlightConfig, SpeedPreset
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
        surface.blit(shadow_image, rect.move(theme.PIXEL_SCALE, theme.PIXEL_SCALE))
    surface.blit(image, rect)
    return rect


class Hud:
    """Draws the output-resolution HUD in the game's pixel-art language."""

    def __init__(self, config: FlightConfig, size: tuple[int, int]) -> None:
        self._config = config
        self._width, self._height = size
        self._menu_overlay = self._make_overlay(48)
        self._pause_overlay = self._make_overlay(150)

    def _make_overlay(self, alpha: int) -> pygame.Surface:
        overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((6, 10, 18, alpha))
        return overlay

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
        bar = pygame.Rect(40, theme.snap(label_rect.bottom + 4), 304, 16)
        theme.pixel_panel(surface, bar, theme.STAMINA_TRACK, cut=4)
        fill_width = theme.snap((bar.width - 8) * fraction)
        if fill_width > 0:
            fill = pygame.Rect(bar.x + 4, bar.y + 4, fill_width, bar.height - 8)
            color = theme.STAMINA_LOW if fraction < 0.25 else theme.STAMINA_FILL
            pygame.draw.rect(surface, color, fill)
        theme.pixel_panel(
            surface,
            bar,
            None,
            border=theme.STAMINA_BORDER,
            cut=4,
            border_width=1,
        )

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
        surface.blit(self._menu_overlay, (0, 0))

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
            translator.text(TextKey.MENU_CONTROLS_FLIGHT),
            19,
            theme.TEXT_MUTED,
            ("center", (self._width // 2, self._height - 92)),
        )
        _draw_text(
            surface,
            translator.text(TextKey.MENU_CONTROLS_SETTINGS),
            19,
            theme.TEXT_MUTED,
            ("center", (self._width // 2, self._height - 72)),
        )
        _draw_text(
            surface,
            self._speed_text(state, translator),
            18,
            theme.TEXT_MUTED,
            ("bottomleft", (40, self._height - 34)),
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
        panel = pygame.Rect(0, 0, 528, 208)
        panel.center = (self._width // 2, self._height // 2)
        theme.pixel_panel(surface, panel, theme.PANEL, border=theme.PANEL_BORDER, cut=16)
        inner = panel.inflate(-theme.PIXEL_SCALE * 2, -theme.PIXEL_SCALE * 2)
        theme.pixel_panel(surface, inner, None, border=theme.PANEL_INNER, cut=12, border_width=1)
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
        panel = pygame.Rect(0, 0, 640, 352)
        panel.center = (self._width // 2, self._height // 2)
        theme.pixel_panel(surface, panel, theme.PANEL, border=theme.PANEL_BORDER, cut=16)
        inner = panel.inflate(-theme.PIXEL_SCALE * 2, -theme.PIXEL_SCALE * 2)
        theme.pixel_panel(surface, inner, None, border=theme.PANEL_INNER, cut=12, border_width=1)

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
        _draw_text(
            surface,
            self._speed_text(state, translator),
            20,
            theme.TEXT_MUTED,
            ("center", (panel.centerx, panel.bottom - 74)),
        )

    def _overlay(self, surface: pygame.Surface) -> None:
        surface.blit(self._pause_overlay, (0, 0))

    @staticmethod
    def _speed_text(state: SessionState, translator: Translator) -> str:
        preset_labels = {
            SpeedPreset.CALM: TextKey.SPEED_CALM,
            SpeedPreset.NORMAL: TextKey.SPEED_NORMAL,
            SpeedPreset.SWIFT: TextKey.SPEED_SWIFT,
        }
        label = translator.text(preset_labels[state.speed])
        return f"{translator.text(TextKey.SPEED_LABEL)}: {label}"

    @staticmethod
    def _record_value(best: int | None, translator: Translator) -> str:
        if best is None:
            return translator.text(TextKey.BEST_EMPTY)
        return f"{best} {translator.text(TextKey.UNIT_M)}"
