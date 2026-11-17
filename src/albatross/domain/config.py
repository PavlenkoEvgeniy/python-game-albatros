"""Tuning constants for the flight simulation.

The simulation works in metres and seconds; rendering converts metres to pixels.
Keeping every knob in one frozen object makes the game easy to tune without
touching the rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class SpeedPreset(StrEnum):
    """Named game-speed settings the player picks between runs."""

    CALM = "calm"
    NORMAL = "normal"
    SWIFT = "swift"


#: How much faster than normal each preset plays. The factor scales every
#: motion rate of the flight, so a preset is a coherent fast-forward or
#: slow-motion of the whole game rather than a single knob.
SPEED_FACTORS: Final[dict[SpeedPreset, float]] = {
    SpeedPreset.CALM: 0.7,
    SpeedPreset.NORMAL: 1.0,
    SpeedPreset.SWIFT: 1.4,
}

SPEED_CYCLE: Final[tuple[SpeedPreset, ...]] = (
    SpeedPreset.CALM,
    SpeedPreset.NORMAL,
    SpeedPreset.SWIFT,
)


def next_speed(current: SpeedPreset) -> SpeedPreset:
    """Return the preset that follows ``current`` in the settings cycle."""
    return SPEED_CYCLE[(SPEED_CYCLE.index(current) + 1) % len(SPEED_CYCLE)]


@dataclass(frozen=True, slots=True)
class FlightConfig:
    """All tunable flight parameters.

    ``vertical_speed_mps`` follows the screen convention used by the domain:
    positive means descending, negative means climbing.
    """

    start_altitude_m: float = 50.0
    horizontal_speed_mps: float = 40.0
    glide_accel_mps2: float = 6.0
    glide_sink_mps: float = 3.4
    flap_up_speed_mps: float = 14.0
    flap_cooldown_s: float = 0.2
    stamina_max: float = 100.0
    flap_stamina_cost: float = 20.0
    meters_to_pixels: float = 8.0
    step_s: float = 1.0 / 120.0
    max_frame_s: float = 0.25
    speed: SpeedPreset = SpeedPreset.NORMAL

    def __post_init__(self) -> None:
        positive = (
            self.start_altitude_m,
            self.horizontal_speed_mps,
            self.glide_accel_mps2,
            self.glide_sink_mps,
            self.flap_up_speed_mps,
            self.flap_cooldown_s,
            self.stamina_max,
            self.flap_stamina_cost,
            self.meters_to_pixels,
            self.step_s,
            self.max_frame_s,
        )
        if min(positive) <= 0.0:
            raise ValueError("all flight parameters must be positive")
        if self.flap_stamina_cost > self.stamina_max:
            raise ValueError("flap_stamina_cost must not exceed stamina_max")
        if self.step_s > self.max_frame_s:
            raise ValueError("step_s must not exceed max_frame_s")


DEFAULT_FLIGHT_CONFIG: Final[FlightConfig] = FlightConfig()
