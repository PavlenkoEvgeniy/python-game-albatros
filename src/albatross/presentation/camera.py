"""World-to-screen projection with a soft vertical follow."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class Camera:
    """Keeps the bird near the left third of the screen.

    Horizontal tracking is exact so the bird stays on its anchor while the world
    scrolls; vertical tracking is smoothed so a flap does not jerk the horizon.
    """

    width: int
    height: int
    pixels_per_meter: float
    anchor_x_ratio: float = 0.26
    anchor_y_ratio: float = 0.40
    smoothing_tau_s: float = 0.16
    x_m: float = 0.0
    altitude_m: float = 0.0
    initialized: bool = False

    def target_x(self, world_x_m: float) -> float:
        return world_x_m - self.anchor_x_ratio * self.width / self.pixels_per_meter

    def target_altitude(self, altitude_m: float) -> float:
        offset = (0.5 - self.anchor_y_ratio) * self.height / self.pixels_per_meter
        return max(0.0, altitude_m - offset)

    def follow(self, world_x_m: float, altitude_m: float, dt: float) -> None:
        """Move the camera towards the bird.

        The first call snaps so the first rendered frame is already framed.
        """
        target_x = self.target_x(world_x_m)
        target_altitude = self.target_altitude(altitude_m)

        if not self.initialized:
            self.x_m = target_x
            self.altitude_m = target_altitude
            self.initialized = True
            return

        self.x_m = target_x
        if dt > 0.0:
            blend = 1.0 - math.exp(-dt / self.smoothing_tau_s)
            self.altitude_m += (target_altitude - self.altitude_m) * blend

    def screen_x(self, world_x_m: float) -> float:
        return (world_x_m - self.x_m) * self.pixels_per_meter

    def screen_y(self, altitude_m: float) -> float:
        return self.height / 2.0 - (altitude_m - self.altitude_m) * self.pixels_per_meter

    @property
    def ground_y(self) -> float:
        return self.screen_y(0.0)

    def parallax_offset(self, factor: float) -> float:
        return self.x_m * self.pixels_per_meter * factor
