from __future__ import annotations

from dataclasses import replace

import pytest

from albatross.domain.config import DEFAULT_FLIGHT_CONFIG, FlightConfig


def test_default_config_is_usable() -> None:
    config = DEFAULT_FLIGHT_CONFIG
    assert config.start_altitude_m > 0
    assert config.flap_stamina_cost * 5 == config.stamina_max
    assert config.step_s <= config.max_frame_s
    assert config.meters_to_pixels > 0


@pytest.mark.parametrize(
    "field",
    [
        "start_altitude_m",
        "horizontal_speed_mps",
        "glide_accel_mps2",
        "glide_sink_mps",
        "flap_up_speed_mps",
        "flap_cooldown_s",
        "stamina_max",
        "flap_stamina_cost",
        "meters_to_pixels",
        "step_s",
        "max_frame_s",
    ],
)
def test_every_parameter_must_be_positive(field: str) -> None:
    with pytest.raises(ValueError, match="positive"):
        replace(DEFAULT_FLIGHT_CONFIG, **{field: 0.0})


def test_flap_cost_cannot_exceed_stamina() -> None:
    with pytest.raises(ValueError, match="flap_stamina_cost"):
        FlightConfig(stamina_max=10.0, flap_stamina_cost=11.0)


def test_step_cannot_exceed_max_frame() -> None:
    with pytest.raises(ValueError, match="step_s"):
        FlightConfig(step_s=0.5, max_frame_s=0.25)


def test_custom_values_are_preserved() -> None:
    config = FlightConfig(start_altitude_m=7.0, horizontal_speed_mps=3.0)
    assert config.start_altitude_m == 7.0
    assert config.horizontal_speed_mps == 3.0
