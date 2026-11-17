from __future__ import annotations

import array

import pygame
import pytest

from albatross.presentation import audio
from albatross.presentation.audio import (
    NullAudioBackend,
    PygameAudioBackend,
    SoundEngine,
    generate_flap,
    generate_wind,
)


def pcm_samples(buffer: bytes) -> array.array[int]:
    samples = array.array("h")
    samples.frombytes(buffer)
    return samples


def test_flap_buffer_has_expected_format_and_signal() -> None:
    buffer = generate_flap(duration_s=0.05, sample_rate=8_000, channels=2)
    samples = pcm_samples(buffer)

    assert len(buffer) == round(0.05 * 8_000) * 2 * 2
    assert max(samples) > 0
    assert max(abs(sample) for sample in samples) < 32_767


def test_wind_buffer_has_expected_format_and_signal() -> None:
    buffer = generate_wind(duration_s=0.1, sample_rate=8_000, channels=1)
    samples = pcm_samples(buffer)

    assert len(buffer) == round(0.1 * 8_000) * 2
    assert max(samples) > 0
    assert max(abs(sample) for sample in samples) < 32_767


@pytest.mark.parametrize("duration", [0.0, -1.0])
def test_generators_reject_bad_durations(duration: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        generate_flap(duration_s=duration, sample_rate=8_000)
    with pytest.raises(ValueError, match="positive"):
        generate_wind(duration_s=duration, sample_rate=8_000)


@pytest.mark.parametrize(("rate", "channels"), [(0, 2), (8_000, 0)])
def test_generators_reject_bad_format(rate: int, channels: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        generate_flap(sample_rate=rate, channels=channels)
    with pytest.raises(ValueError, match="positive"):
        generate_wind(sample_rate=rate, channels=channels)


def test_null_backend_is_silent_and_toggleable() -> None:
    engine = SoundEngine(NullAudioBackend())
    assert engine.available is False
    assert engine.muted is False

    engine.start()
    engine.on_flap()
    assert engine.toggle_mute() is True
    engine.on_flap()
    assert engine.toggle_mute() is False


class FakeBackend:
    available = True

    def __init__(self) -> None:
        self.flaps = 0
        self.wind_starts = 0
        self.mute_values: list[bool] = []

    def play_flap(self) -> None:
        self.flaps += 1

    def start_wind(self) -> None:
        self.wind_starts += 1

    def set_muted(self, muted: bool) -> None:
        self.mute_values.append(muted)


def test_engine_routes_events_and_mute_to_backend() -> None:
    backend = FakeBackend()
    engine = SoundEngine(backend)

    engine.start()
    engine.on_flap()
    assert backend.wind_starts == 1
    assert backend.flaps == 1

    engine.set_muted(True)
    engine.on_flap()
    assert backend.flaps == 1
    assert backend.mute_values == [True]

    engine.set_muted(False)
    engine.on_flap()
    assert backend.flaps == 2


def test_real_backend_starts_with_dummy_driver() -> None:
    backend = PygameAudioBackend()
    backend.start_wind()
    backend.play_flap()
    backend.set_muted(True)
    backend.set_muted(False)
    backend.start_wind()
    assert backend.available is True


def test_missing_audio_device_falls_back_to_silence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audio.pygame.mixer, "get_init", lambda: None)

    def fail_init(*args: object, **kwargs: object) -> None:
        raise pygame.error("no audio device")

    monkeypatch.setattr(audio.pygame.mixer, "init", fail_init)

    engine = SoundEngine()

    assert engine.available is False
    engine.start()
    engine.on_flap()
