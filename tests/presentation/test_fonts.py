from __future__ import annotations

import pygame

from albatross.presentation.fonts import render_text
from albatross.presentation.i18n import TRANSLATIONS

TEXT_COLOUR = (250, 244, 225)


def test_text_is_rendered_without_anti_aliasing() -> None:
    surface = render_text("Альбатрос", 24, TEXT_COLOUR)
    background = surface.get_colorkey()

    visible_colours = {
        tuple(surface.get_at((x, y)))
        for x in range(surface.get_width())
        for y in range(surface.get_height())
        if tuple(surface.get_at((x, y))) != background
    }
    assert visible_colours == {(*TEXT_COLOUR, 255)}


def test_russian_and_english_text_have_visible_glyphs() -> None:
    russian = render_text("Пробел — взмах", 20, TEXT_COLOUR)
    english = render_text("Space — flap", 20, TEXT_COLOUR)

    assert russian.get_bounding_rect(min_alpha=1).width > 20
    assert english.get_bounding_rect(min_alpha=1).width > 20
    assert isinstance(russian, pygame.Surface)


def test_every_translation_fits_the_game_width_at_large_text_size() -> None:
    for language in TRANSLATIONS.values():
        for text in language.values():
            assert render_text(text, 48, TEXT_COLOUR).get_width() <= 1200
