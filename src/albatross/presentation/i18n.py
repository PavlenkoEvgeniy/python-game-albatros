"""Tiny two-language dictionary.

Two languages and a handful of strings do not justify gettext catalogs. Keys are
an enum so a missing translation fails type checking and a parity test catches
gaps at runtime.
"""

from __future__ import annotations

from enum import StrEnum


class Language(StrEnum):
    RU = "ru"
    EN = "en"


class TextKey(StrEnum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    START_HINT = "start_hint"
    MENU_CONTROLS = "menu_controls"
    DISTANCE_LABEL = "distance_label"
    BEST_LABEL = "best_label"
    BEST_EMPTY = "best_empty"
    STAMINA_LABEL = "stamina_label"
    PAUSED = "paused"
    PAUSE_HINT = "pause_hint"
    GAME_OVER_TITLE = "game_over_title"
    GAME_OVER_SUBTITLE = "game_over_subtitle"
    RESTART_HINT = "restart_hint"
    NEW_RECORD = "new_record"
    UNIT_M = "unit_m"
    PLAY_HINT = "play_hint"
    SOUND_ON = "sound_on"
    SOUND_OFF = "sound_off"


TRANSLATIONS: dict[Language, dict[TextKey, str]] = {
    Language.RU: {
        TextKey.TITLE: "АЛЬБАТРОС",
        TextKey.SUBTITLE: "Полёт над долиной",
        TextKey.START_HINT: "Пробел или клик — начать полёт",
        TextKey.MENU_CONTROLS: (
            "Пробел / клик — взмах   ·   Esc — пауза   ·   L — язык   ·   M — звук"
        ),
        TextKey.DISTANCE_LABEL: "Дистанция",
        TextKey.BEST_LABEL: "Рекорд",
        TextKey.BEST_EMPTY: "—",
        TextKey.STAMINA_LABEL: "Силы",
        TextKey.PAUSED: "Пауза",
        TextKey.PAUSE_HINT: "Esc — продолжить полёт",
        TextKey.GAME_OVER_TITLE: "Приземление",
        TextKey.GAME_OVER_SUBTITLE: "Альбатрос коснулся земли",
        TextKey.RESTART_HINT: "R, пробел или клик — ещё раз",
        TextKey.NEW_RECORD: "Новый рекорд!",
        TextKey.UNIT_M: "м",
        TextKey.PLAY_HINT: "Esc — пауза     L — язык     M — звук",
        TextKey.SOUND_ON: "Звук: вкл",
        TextKey.SOUND_OFF: "Звук: выкл",
    },
    Language.EN: {
        TextKey.TITLE: "ALBATROSS",
        TextKey.SUBTITLE: "Flight over the valley",
        TextKey.START_HINT: "Press Space or click to start",
        TextKey.MENU_CONTROLS: (
            "Space / click — flap   ·   Esc — pause   ·   L — language   ·   M — sound"
        ),
        TextKey.DISTANCE_LABEL: "Distance",
        TextKey.BEST_LABEL: "Best",
        TextKey.BEST_EMPTY: "—",
        TextKey.STAMINA_LABEL: "Stamina",
        TextKey.PAUSED: "Paused",
        TextKey.PAUSE_HINT: "Esc — resume",
        TextKey.GAME_OVER_TITLE: "Grounded",
        TextKey.GAME_OVER_SUBTITLE: "The albatross touched the ground",
        TextKey.RESTART_HINT: "Press R, Space or click to fly again",
        TextKey.NEW_RECORD: "New record!",
        TextKey.UNIT_M: "m",
        TextKey.PLAY_HINT: "Esc — pause     L — language     M — sound",
        TextKey.SOUND_ON: "Sound: on",
        TextKey.SOUND_OFF: "Sound: off",
    },
}


class Translator:
    """Current language and text lookup."""

    def __init__(self, language: Language = Language.RU) -> None:
        self._language = language

    @property
    def language(self) -> Language:
        return self._language

    def toggle(self) -> Language:
        """Switch language and return the new one."""
        self._language = Language.EN if self._language is Language.RU else Language.RU
        return self._language

    def text(self, key: TextKey) -> str:
        return TRANSLATIONS[self._language][key]
