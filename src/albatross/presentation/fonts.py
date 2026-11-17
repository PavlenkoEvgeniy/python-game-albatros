"""Font access with a cached default font.

Pygame ships a default font that contains Cyrillic glyphs; using it keeps the
game asset-free. Sizes are cached because creating fonts is relatively costly.
"""

from __future__ import annotations

from functools import lru_cache

import pygame


@lru_cache(maxsize=32)
def get_font(size: int) -> pygame.font.Font:
    return pygame.font.Font(None, size)


def render_text(text: str, size: int, color: tuple[int, int, int]) -> pygame.Surface:
    """Render crisp, non-anti-aliased text with the built-in font."""
    return get_font(size).render(text, False, color)
