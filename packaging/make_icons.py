"""Generate the application icon from the game's own procedural scene.

Run with Pillow available, for example:

    uv run --with pillow python packaging/make_icons.py

The generated PNG, ICO and ICNS files are committed so CI does not need Pillow.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image

from albatross.presentation import theme
from albatross.presentation.bird import Bird

SIZE = 512
ROOT = Path(__file__).resolve().parent
ICON_DIR = ROOT / "icons"
LINUX_DIR = ROOT / "linux"


def draw_icon() -> pygame.Surface:
    icon = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    mask = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, SIZE, SIZE), border_radius=104)

    sky = theme.vertical_gradient(SIZE, SIZE, theme.SKY_TOP, theme.SKY_HORIZON)
    sky.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    icon.blit(sky, (0, 0))

    for radius, alpha in ((96, 26), (72, 40), (52, 70)):
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*theme.SUN_GLOW, alpha), (radius, radius), radius)
        icon.blit(glow, (352 - radius, 128 - radius))
    pygame.draw.circle(icon, theme.SUN_CORE, (352, 128), 42)

    pygame.draw.polygon(
        icon,
        theme.MOUNTAIN_FAR,
        [(0, 360), (90, 250), (180, 350), (275, 235), (390, 360), (512, 280), (512, 512), (0, 512)],
    )
    pygame.draw.polygon(
        icon,
        theme.MOUNTAIN_MID,
        [
            (0, 430),
            (130, 320),
            (245, 420),
            (340, 330),
            (470, 430),
            (512, 400),
            (512, 512),
            (0, 512),
        ],
    )
    pygame.draw.rect(icon, theme.GROUND_TOP, (0, 455, SIZE, SIZE - 455))
    pygame.draw.line(icon, theme.GROUND_LINE, (0, 455), (SIZE, 455), 4)

    bird = Bird()
    bird.draw(icon, (262, 350), vertical_speed=0.0)
    return icon


def main() -> None:
    pygame.init()
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    LINUX_DIR.mkdir(parents=True, exist_ok=True)

    surface = draw_icon()
    png_path = ICON_DIR / "albatross.png"
    pygame.image.save(surface, png_path)

    image = Image.open(png_path).convert("RGBA")
    image.save(
        ICON_DIR / "albatross.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    image.save(ICON_DIR / "albatross.icns", format="ICNS")
    image.save(LINUX_DIR / "albatross.png")
    pygame.quit()
    print(f"icons written to {ICON_DIR}")


if __name__ == "__main__":
    main()
