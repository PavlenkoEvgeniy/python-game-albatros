from __future__ import annotations

from albatross.presentation.fonts import get_font
from albatross.presentation.i18n import (
    TRANSLATIONS,
    Language,
    TextKey,
    Translator,
)


def test_both_languages_define_every_key() -> None:
    assert set(TRANSLATIONS[Language.RU]) == set(TextKey)
    assert set(TRANSLATIONS[Language.EN]) == set(TextKey)


def test_no_translation_is_empty() -> None:
    for language in Language:
        for key in TextKey:
            assert TRANSLATIONS[language][key].strip()


def test_translator_defaults_to_russian_and_toggles() -> None:
    translator = Translator()
    assert translator.language is Language.RU
    assert translator.text(TextKey.TITLE) == "АЛЬБАТРОС"
    assert translator.toggle() is Language.EN
    assert translator.text(TextKey.TITLE) == "ALBATROSS"
    assert translator.toggle() is Language.RU


def test_default_font_has_every_glyph() -> None:
    font = get_font(24)
    for language in Language:
        for text in TRANSLATIONS[language].values():
            metrics = font.metrics(text)
            assert metrics is not None
            assert all(metric is not None for metric in metrics), text
            assert font.size(text)[0] > 0


def test_custom_language_is_respected() -> None:
    translator = Translator(Language.EN)
    assert translator.text(TextKey.PAUSED) == "Paused"


def test_font_rendering_has_visible_pixels() -> None:
    image = get_font(32).render("Альбатрос", True, (255, 255, 255))
    assert image.get_width() > 0
    assert image.get_height() > 0
    assert image.get_at((image.get_width() // 2, image.get_height() // 2))[3] > 0
