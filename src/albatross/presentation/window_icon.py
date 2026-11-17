"""Window icon setup with an X11 _NET_WM_ICON fallback.

SDL normally handles the icon, but some X11/Xwayland combinations accept
``set_icon`` without publishing the EWMH property. The fallback uses libX11 via
ctypes so no new runtime dependency is introduced.
"""

from __future__ import annotations

import ctypes

import pygame

from albatross.presentation.icon import make_icon

_WM_ICON_SIZES = (16, 32, 48, 64, 128, 256)
_XA_CARDINAL = 6
_PROP_MODE_REPLACE = 0


def _icon_cardinals() -> list[int]:
    values: list[int] = []
    for size in _WM_ICON_SIZES:
        values.extend((size, size))
        raw = pygame.image.tobytes(make_icon(size), "RGBA")
        for index in range(0, len(raw), 4):
            alpha = raw[index + 3]
            if alpha == 0:
                values.append(0)
            else:
                values.append(
                    (alpha << 24) | (raw[index] << 16) | (raw[index + 1] << 8) | raw[index + 2]
                )
    return values


def _publish_x11_icon(window: int, values: list[int]) -> None:
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XChangeProperty.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.c_int,
    ]
    x11.XFlush.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]

    display = x11.XOpenDisplay(None)
    if not display:
        raise OSError("cannot open the X11 display")
    try:
        icon_atom = x11.XInternAtom(display, b"_NET_WM_ICON", 0)
        cardinal_atom = x11.XInternAtom(display, b"CARDINAL", 0)
        payload = (ctypes.c_ulong * len(values))(*values)
        x11.XChangeProperty(
            display,
            window,
            icon_atom,
            cardinal_atom or _XA_CARDINAL,
            32,
            _PROP_MODE_REPLACE,
            payload,
            len(values),
        )
        x11.XFlush(display)
    finally:
        x11.XCloseDisplay(display)


def apply_window_icon() -> None:
    """Set the window icon, then repair the X11 property when needed."""
    pygame.display.set_icon(make_icon(64))
    if pygame.display.get_driver() != "x11":
        return
    try:
        window = pygame.display.get_wm_info().get("window")
        if isinstance(window, int):
            _publish_x11_icon(window, _icon_cardinals())
    except (OSError, AttributeError, TypeError, ValueError):
        # A missing or restricted X11 library must never prevent the game from
        # starting; the desktop entry still supplies a packaged icon.
        return
