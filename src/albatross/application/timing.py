"""Frame-time accumulation for a fixed simulation step."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FixedStepClock:
    """Turns variable frame deltas into a whole number of fixed steps.

    A long frame (window drag, debugger) is clamped so the bird never teleports
    across the world. Leftover time is carried into the next frame, keeping the
    simulation speed independent of the frame rate.
    """

    step_s: float
    max_frame_s: float
    _accumulator_s: float = 0.0

    def feed(self, frame_s: float) -> int:
        clamped = min(max(0.0, frame_s), self.max_frame_s)
        self._accumulator_s += clamped
        steps = int(self._accumulator_s / self.step_s)
        self._accumulator_s -= steps * self.step_s
        return steps
