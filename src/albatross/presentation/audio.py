"""Procedural sound: a flap whoosh and looping wind, generated at runtime.

No audio files are shipped. If the mixer cannot start the game keeps working
with a silent backend.
"""

from __future__ import annotations

import array
import math
import random
from typing import Protocol

import pygame

SAMPLE_RATE = 44_100
CHANNELS = 2
SAMPLE_WIDTH = 2


def _pack(samples: list[float], channels: int = CHANNELS) -> bytes:
    """Convert mono float samples in ``[-1, 1]`` to signed 16-bit PCM."""
    pcm = array.array("h")
    for sample in samples:
        value = round(max(-1.0, min(1.0, sample)) * 32_767)
        for _ in range(channels):
            pcm.append(value)
    return pcm.tobytes()


def generate_flap(
    duration_s: float = 0.22,
    sample_rate: int = SAMPLE_RATE,
    channels: int = CHANNELS,
    seed: int = 11,
) -> bytes:
    """A short filtered-noise whoosh with a fast attack and soft decay."""
    if duration_s <= 0.0 or sample_rate <= 0 or channels <= 0:
        raise ValueError("duration, sample rate and channels must be positive")

    rng = random.Random(seed)
    frames = round(duration_s * sample_rate)
    samples: list[float] = []
    filtered = 0.0
    for index in range(frames):
        t = index / sample_rate
        attack = min(1.0, t / 0.012)
        decay = max(0.0, 1.0 - t / duration_s) ** 2.1
        filtered = filtered * 0.62 + rng.uniform(-1.0, 1.0) * 0.38
        tone = 0.18 * math.sin(math.tau * 118.0 * t)
        samples.append((filtered + tone) * attack * decay * 0.85)
    return _pack(samples, channels)


def generate_wind(
    duration_s: float = 1.8,
    sample_rate: int = SAMPLE_RATE,
    channels: int = CHANNELS,
    seed: int = 23,
) -> bytes:
    """A seamless loop made from partials whose periods divide the duration."""
    if duration_s <= 0.0 or sample_rate <= 0 or channels <= 0:
        raise ValueError("duration, sample rate and channels must be positive")

    rng = random.Random(seed)
    base = 1.0 / duration_s
    tones = [
        (k * base, rng.uniform(0.4, 1.0) / math.sqrt(k), rng.uniform(0.0, math.tau))
        for k in rng.sample(range(26, 190), 14)
    ]
    modulation_frequency = 17 * base
    frames = round(duration_s * sample_rate)
    samples: list[float] = []
    for index in range(frames):
        t = index / sample_rate
        value = sum(
            amplitude * math.sin(math.tau * frequency * t + phase)
            for frequency, amplitude, phase in tones
        )
        modulation = 0.62 + 0.38 * math.sin(math.tau * modulation_frequency * t + 0.9)
        samples.append(value * modulation)
    peak = max(abs(sample) for sample in samples)
    scale = 0.34 / peak if peak > 0.0 else 0.0
    return _pack([sample * scale for sample in samples], channels)


class AudioBackend(Protocol):
    @property
    def available(self) -> bool: ...

    def play_flap(self) -> None: ...

    def start_wind(self) -> None: ...

    def set_muted(self, muted: bool) -> None: ...


class NullAudioBackend:
    """Silent backend used when no audio device can be opened."""

    available = False

    def play_flap(self) -> None:
        pass

    def start_wind(self) -> None:
        pass

    def set_muted(self, muted: bool) -> None:
        pass


class PygameAudioBackend:
    """pygame.mixer implementation backed by generated buffers."""

    available = True
    WIND_VOLUME = 0.28
    FLAP_VOLUME = 0.42

    def __init__(self) -> None:
        self._flap = pygame.mixer.Sound(buffer=generate_flap())
        self._wind = pygame.mixer.Sound(buffer=generate_wind())
        self._wind_channel: pygame.mixer.Channel | None = None
        self._muted = False

    def play_flap(self) -> None:
        self._flap.set_volume(self.FLAP_VOLUME)
        self._flap.play()

    def start_wind(self) -> None:
        if self._wind_channel is None or not self._wind_channel.get_busy():
            self._wind_channel = self._wind.play(loops=-1)
        self._apply_volume()

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        self._apply_volume()

    def _apply_volume(self) -> None:
        if self._wind_channel is not None:
            self._wind_channel.set_volume(0.0 if self._muted else self.WIND_VOLUME)


class SoundEngine:
    """Mute state and high-level sound events."""

    def __init__(self, backend: AudioBackend | None = None) -> None:
        self._backend = backend if backend is not None else self._build_backend()
        self._muted = False

    @property
    def available(self) -> bool:
        return self._backend.available

    @property
    def muted(self) -> bool:
        return self._muted

    def start(self) -> None:
        self._backend.start_wind()

    def on_flap(self) -> None:
        if not self._muted:
            self._backend.play_flap()

    def toggle_mute(self) -> bool:
        self.set_muted(not self._muted)
        return self._muted

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        self._backend.set_muted(muted)

    def _build_backend(self) -> AudioBackend:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=SAMPLE_RATE,
                    size=-16,
                    channels=CHANNELS,
                )
            return PygameAudioBackend()
        except Exception:
            return NullAudioBackend()
