from __future__ import annotations

from pathlib import Path

import pygame
from PIL import Image

from albatross.presentation.icon import ICON_SIZES, make_icon

ROOT = Path(__file__).resolve().parents[2]
ICON_DIR = ROOT / "packaging" / "icons"
LINUX_DIR = ICON_DIR / "linux"


def test_primary_png_has_expected_size_and_transparency() -> None:
    with Image.open(ICON_DIR / "albatross.png") as image:
        assert image.size == (512, 512)
        assert image.mode == "RGBA"
        assert image.getpixel((0, 0))[3] == 0
        assert image.getpixel((256, 256))[3] == 255


def test_ico_contains_every_required_native_size() -> None:
    with Image.open(ICON_DIR / "albatross.ico") as image:
        assert image.info["sizes"] == {
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        }


def test_icns_contains_standard_macos_sizes() -> None:
    with Image.open(ICON_DIR / "albatross.icns") as image:
        sizes = {(entry[0], entry[1]) for entry in image.info["sizes"]}
        assert sizes == {(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512)}


def test_linux_hicolor_files_are_native_pixel_renders() -> None:
    for size in ICON_SIZES:
        path = LINUX_DIR / f"{size}x{size}" / "albatross.png"
        with Image.open(path) as image:
            assert image.size == (size, size)
            assert image.tobytes() == pygame.image.tobytes(make_icon(size), "RGBA")


def test_linux_legacy_png_matches_the_512_master() -> None:
    assert (ROOT / "packaging" / "linux" / "albatross.png").read_bytes() == (
        ICON_DIR / "albatross.png"
    ).read_bytes()
