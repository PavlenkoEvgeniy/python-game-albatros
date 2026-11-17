from __future__ import annotations

import json
from pathlib import Path

import pytest
from platformdirs import user_data_dir

from albatross.infrastructure import records
from albatross.infrastructure.records import RecordStore


def test_default_path_is_in_the_platform_data_directory() -> None:
    store = RecordStore()
    expected = Path(user_data_dir("albatross", appauthor=False)) / "record.json"
    assert store.path == expected


def test_missing_file_means_no_record(tmp_path: Path) -> None:
    assert RecordStore(tmp_path / "record.json").load_best() is None


def test_unreadable_path_means_no_record(tmp_path: Path) -> None:
    directory = tmp_path / "record.json"
    directory.mkdir()
    assert RecordStore(directory).load_best() is None


def test_valid_record_is_loaded(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    path.write_text('{"version": 1, "best_distance_m": 1234}', encoding="utf-8")
    assert RecordStore(path).load_best() == 1234


def test_zero_is_a_valid_record(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    path.write_text('{"version": 1, "best_distance_m": 0}', encoding="utf-8")
    assert RecordStore(path).load_best() == 0


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '{"best_distance_m": 10}',
        '{"version": 2, "best_distance_m": 10}',
        '{"version": 1, "best_distance_m": true}',
        '{"version": 1, "best_distance_m": "10"}',
        '{"version": 1, "best_distance_m": 1.5}',
        '{"version": 1, "best_distance_m": -1}',
        '{"version": 1}',
    ],
)
def test_invalid_record_means_no_record(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "record.json"
    path.write_text(payload, encoding="utf-8")
    assert RecordStore(path).load_best() is None


def test_save_creates_directories_and_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "data" / "record.json"
    store = RecordStore(path)

    store.save_best(987)

    assert store.load_best() == 987
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "version": 1,
        "best_distance_m": 987,
    }


def test_negative_record_is_rejected(tmp_path: Path) -> None:
    store = RecordStore(tmp_path / "record.json")
    with pytest.raises(ValueError, match="negative"):
        store.save_best(-1)
    assert not store.path.exists()


def test_failed_replace_keeps_the_previous_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = RecordStore(tmp_path / "record.json")
    store.save_best(100)

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(records.os, "replace", fail_replace)

    with pytest.raises(OSError, match="disk full"):
        store.save_best(200)

    assert store.load_best() == 100
    assert list(tmp_path.glob("*.tmp")) == []
