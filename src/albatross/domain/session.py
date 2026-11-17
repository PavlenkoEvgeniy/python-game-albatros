"""Game session state machine.

The session owns the current phase and the flight snapshot. It has no notion of
time sources, rendering or input devices: the application feeds it commands and
fixed-size time steps.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from albatross.domain.config import DEFAULT_FLIGHT_CONFIG, FlightConfig, SpeedPreset
from albatross.domain.flight import FlightModel, FlightState
from albatross.domain.scoring import updated_best


class GamePhase(StrEnum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


@dataclass(frozen=True, slots=True)
class SessionState:
    phase: GamePhase
    flight: FlightState
    best_distance_m: int | None
    last_distance_m: int | None
    new_record: bool = False
    speed: SpeedPreset = SpeedPreset.NORMAL


class GameSession:
    """Phase transitions and command handling for one process lifetime."""

    def __init__(
        self,
        config: FlightConfig = DEFAULT_FLIGHT_CONFIG,
        best_distance_m: int | None = None,
    ) -> None:
        self._model = FlightModel(config)
        self._state = SessionState(
            phase=GamePhase.MENU,
            flight=self._model.initial_state(),
            best_distance_m=best_distance_m,
            last_distance_m=None,
            speed=config.speed,
        )

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def config(self) -> FlightConfig:
        return self._model.config

    def start(self) -> bool:
        """Start a run from the menu."""
        if self._state.phase is not GamePhase.MENU:
            return False
        self._state = replace(
            self._state,
            phase=GamePhase.PLAYING,
            flight=self._model.initial_state(),
            last_distance_m=None,
            new_record=False,
        )
        return True

    def request_flap(self) -> bool:
        """Try to flap; return whether the action was accepted."""
        if self._state.phase is not GamePhase.PLAYING:
            return False
        flight, accepted = self._model.flap(self._state.flight)
        if accepted:
            self._state = replace(self._state, flight=flight)
        return accepted

    def set_speed(self, preset: SpeedPreset) -> bool:
        """Switch the speed preset; only allowed between runs.

        Changing the physics mid-flight would alter a run in progress, so the
        setting applies from the next run onward (menu or game-over screen).
        """
        if self._state.phase not in (GamePhase.MENU, GamePhase.GAME_OVER):
            return False
        if preset is self._model.config.speed:
            return False
        self._model = FlightModel(replace(self._model.config, speed=preset))
        self._state = replace(self._state, speed=preset)
        return True

    def toggle_pause(self) -> bool:
        """Toggle between playing and paused; ignore other phases."""
        if self._state.phase is GamePhase.PLAYING:
            self._state = replace(self._state, phase=GamePhase.PAUSED)
            return True
        if self._state.phase is GamePhase.PAUSED:
            self._state = replace(self._state, phase=GamePhase.PLAYING)
            return True
        return False

    def restart(self) -> bool:
        """Start a fresh run after the previous one ended."""
        if self._state.phase is not GamePhase.GAME_OVER:
            return False
        self._state = replace(
            self._state,
            phase=GamePhase.PLAYING,
            flight=self._model.initial_state(),
            last_distance_m=None,
            new_record=False,
        )
        return True

    def advance(self, dt: float) -> bool:
        """Advance the simulation while playing.

        Returns ``True`` when the simulation was stepped. On touch-down the phase
        becomes ``GAME_OVER``, the finished distance is recorded and the best
        result is updated.
        """
        if self._state.phase is not GamePhase.PLAYING:
            return False

        flight = self._model.advance(self._state.flight, dt)
        if flight.grounded:
            distance_m = flight.distance_m
            best_before = self._state.best_distance_m
            self._state = replace(
                self._state,
                phase=GamePhase.GAME_OVER,
                flight=flight,
                best_distance_m=updated_best(best_before, distance_m),
                last_distance_m=distance_m,
                new_record=best_before is None or distance_m > best_before,
            )
        else:
            self._state = replace(self._state, flight=flight)
        return True
