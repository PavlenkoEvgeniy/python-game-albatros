"""Deterministic flight simulation.

The model is intentionally simple: while gliding, vertical speed relaxes
towards a terminal sink rate; a flap replaces it with a fixed upward speed.
This gives smooth, predictable arcs and invariants that are easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from albatross.domain.config import FlightConfig


@dataclass(frozen=True, slots=True)
class FlightState:
    """One immutable snapshot of the bird's flight."""

    x_m: float
    altitude_m: float
    vertical_speed_mps: float
    stamina: float
    cooldown_s: float
    grounded: bool = False

    @property
    def distance_m(self) -> int:
        """Horizontal distance from the launch point, in whole metres."""
        return int(self.x_m)


class FlightModel:
    """Pure flight rules operating on immutable states."""

    def __init__(self, config: FlightConfig) -> None:
        self._config = config

    @property
    def config(self) -> FlightConfig:
        return self._config

    def initial_state(self) -> FlightState:
        """Return the state at the start of a run: high, level and fully rested."""
        return FlightState(
            x_m=0.0,
            altitude_m=self._config.start_altitude_m,
            vertical_speed_mps=0.0,
            stamina=self._config.stamina_max,
            cooldown_s=0.0,
            grounded=False,
        )

    def advance(self, state: FlightState, dt: float) -> FlightState:
        """Advance the flight by ``dt`` seconds.

        A grounded state or a non-positive ``dt`` is returned unchanged. Once the
        bird reaches the ground the state freezes: position, speed and stamina no
        longer change.
        """
        if state.grounded or dt <= 0.0:
            return state

        cooldown = max(0.0, state.cooldown_s - dt)
        vertical_speed = min(
            state.vertical_speed_mps + self._config.glide_accel_mps2 * dt,
            self._config.glide_sink_mps,
        )
        altitude = state.altitude_m - vertical_speed * dt
        x_m = state.x_m + self._config.horizontal_speed_mps * dt

        if altitude <= 0.0:
            return FlightState(
                x_m=x_m,
                altitude_m=0.0,
                vertical_speed_mps=0.0,
                stamina=state.stamina,
                cooldown_s=0.0,
                grounded=True,
            )

        return replace(
            state,
            x_m=x_m,
            altitude_m=altitude,
            vertical_speed_mps=vertical_speed,
            cooldown_s=cooldown,
        )

    def flap(self, state: FlightState) -> tuple[FlightState, bool]:
        """Apply a wing flap if the bird is airborne, rested and off cooldown."""
        if (
            state.grounded
            or state.cooldown_s > 0.0
            or state.stamina < self._config.flap_stamina_cost
        ):
            return state, False

        return (
            replace(
                state,
                vertical_speed_mps=-self._config.flap_up_speed_mps,
                stamina=state.stamina - self._config.flap_stamina_cost,
                cooldown_s=self._config.flap_cooldown_s,
            ),
            True,
        )
