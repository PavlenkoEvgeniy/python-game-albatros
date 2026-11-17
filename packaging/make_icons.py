"""Generate all delivery icons from the game's shared pixel-art generator.

Run from the repository root:

    uv run python packaging/make_icons.py

The generated files are committed, so CI and ordinary builds do not need
Pillow. Each ICO/ICNS entry is built from a native-size render rather than
downsampling a blurry master.
"""

from __future__ import annotations

import math
import os
import struct
from io import BytesIO
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image, ImageDraw

from albatross.presentation.icon import ICON_SIZES, make_icon

ROOT = Path(__file__).resolve().parent
ICON_DIR = ROOT / "icons"
LINUX_DIR = ROOT / "linux"
LINUX_ICON_DIR = ICON_DIR / "linux"
BUILD_DIR = ROOT.parent / "build"
ICO_SIZES = tuple(size for size in ICON_SIZES if size <= 256)
ICNS_TYPES = {
    16: b"icp4",
    32: b"icp5",
    64: b"icp6",
    128: b"ic07",
    256: b"ic08",
    512: b"ic09",
}


def _png_bytes(surface: pygame.Surface) -> bytes:
    width, height = surface.get_size()
    image = Image.frombytes("RGBA", (width, height), pygame.image.tobytes(surface, "RGBA"))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _write_ico(path: Path, payloads: dict[int, bytes]) -> None:
    sizes = sorted(payloads)
    if not sizes:
        raise ValueError("an ICO needs at least one size")
    header = struct.pack("<HHH", 0, 1, len(sizes))
    offset = len(header) + 16 * len(sizes)
    entries = bytearray()
    body = bytearray()
    for size in sizes:
        data = payloads[size]
        dimension = 0 if size == 256 else size
        entries.extend(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(data),
                offset,
            )
        )
        body.extend(data)
        offset += len(data)
    path.write_bytes(header + entries + body)


def _write_icns(path: Path, payloads: dict[int, bytes]) -> None:
    chunks = bytearray()
    for size, icon_type in ICNS_TYPES.items():
        data = payloads[size]
        chunks.extend(icon_type)
        chunks.extend(struct.pack(">I", len(data) + 8))
        chunks.extend(data)
    path.write_bytes(b"icns" + struct.pack(">I", len(chunks) + 8) + chunks)


def _write_contact_sheet(payloads: dict[int, bytes]) -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (1200, 640), (24, 29, 36, 255))
    draw = ImageDraw.Draw(sheet)

    large = Image.open(BytesIO(payloads[512])).convert("RGBA")
    sheet.alpha_composite(large, (16, 64))
    draw.text((16, 16), "Albatross icon — 512px", fill=(240, 235, 220, 255))

    y = 16
    for size in (256, 128, 64, 48, 32, 24, 16):
        icon = Image.open(BytesIO(payloads[size])).convert("RGBA")
        sheet.alpha_composite(icon, (560, y))
        draw.text(
            (560 + size + 12, y + max(0, size // 2 - 6)), f"{size}px", fill=(220, 216, 202, 255)
        )
        y += size + 8
    path = BUILD_DIR / "icon_contact_sheet.png"
    sheet.save(path)
    return path


def generate() -> tuple[dict[int, bytes], Path]:
    pygame.init()
    try:
        surfaces = {size: make_icon(size) for size in ICON_SIZES}
        payloads = {size: _png_bytes(surface) for size, surface in surfaces.items()}

        ICON_DIR.mkdir(parents=True, exist_ok=True)
        LINUX_DIR.mkdir(parents=True, exist_ok=True)
        (ICON_DIR / "albatross.png").write_bytes(payloads[512])
        (LINUX_DIR / "albatross.png").write_bytes(payloads[512])
        _write_ico(ICON_DIR / "albatross.ico", {size: payloads[size] for size in ICO_SIZES})
        _write_icns(ICON_DIR / "albatross.icns", payloads)

        for size in ICON_SIZES:
            target = LINUX_ICON_DIR / f"{size}x{size}" / "albatross.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payloads[size])

        contact_sheet = _write_contact_sheet(payloads)
        return payloads, contact_sheet
    finally:
        pygame.quit()


def main() -> None:
    payloads, contact_sheet = generate()
    total = sum(len(data) for data in payloads.values())
    print(f"icons written to {ICON_DIR} ({len(payloads)} sizes, {math.ceil(total / 1024)} KiB)")
    print(f"Linux hicolor set written to {LINUX_ICON_DIR}")
    print(f"contact sheet: {contact_sheet}")


if __name__ == "__main__":
    main()
