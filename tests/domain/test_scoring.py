from __future__ import annotations

from albatross.domain.scoring import updated_best


def test_first_result_becomes_the_record() -> None:
    assert updated_best(None, 120) == 120


def test_better_result_replaces_the_record() -> None:
    assert updated_best(120, 121) == 121


def test_weaker_or_equal_result_keeps_the_record() -> None:
    assert updated_best(120, 119) == 120
    assert updated_best(120, 120) == 120
