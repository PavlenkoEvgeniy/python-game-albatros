from __future__ import annotations

import pygame
import pytest

from albatross.presentation import window_icon


def test_window_icon_uses_pygame_on_non_x11(monkeypatch: pytest.MonkeyPatch) -> None:
    installed: list[pygame.Surface] = []
    monkeypatch.setattr(pygame.display, "set_icon", installed.append)
    monkeypatch.setattr(pygame.display, "get_driver", lambda: "wayland")

    window_icon.apply_window_icon()

    assert len(installed) == 1
    assert installed[0].get_size() == (64, 64)


def test_icon_cardinals_include_each_dimension_and_argb_pixels() -> None:
    values = window_icon._icon_cardinals()

    expected_length = sum(2 + size * size for size in (16, 32, 48, 64, 128, 256))
    assert len(values) == expected_length
    assert values[:2] == [16, 16]


def test_x11_publish_failure_does_not_prevent_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pygame.display, "set_icon", lambda surface: None)
    monkeypatch.setattr(pygame.display, "get_driver", lambda: "x11")
    monkeypatch.setattr(pygame.display, "get_wm_info", lambda: {"window": 1})

    def fail_publish(window: int, values: list[int]) -> None:
        raise OSError("no libX11")

    monkeypatch.setattr(window_icon, "_publish_x11_icon", fail_publish)

    window_icon.apply_window_icon()
