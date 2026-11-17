"""Persistent best-result storage.

The file lives in the platform's user-data directory. Reads are defensive: a
missing, malformed or foreign file simply means "no record yet". Writes are
atomic so an interrupted save can never replace a valid record with a partial
one.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from platformdirs import user_data_dir

RECORD_FILE_NAME = "record.json"
RECORD_VERSION = 1


class RecordStore:
    """Load and atomically save the player's best distance."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = (
            path
            if path is not None
            else Path(user_data_dir("albatross", appauthor=False)) / RECORD_FILE_NAME
        )

    @property
    def path(self) -> Path:
        return self._path

    def load_best(self) -> int | None:
        """Return the stored best distance, or ``None`` when there is none."""
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError:
            return None

        try:
            data = json.loads(text)
        except ValueError:
            return None

        if not isinstance(data, dict):
            return None
        if data.get("version") != RECORD_VERSION:
            return None

        value = data.get("best_distance_m")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value

    def save_best(self, best_distance_m: int) -> None:
        """Atomically write ``best_distance_m`` as the current record."""
        if best_distance_m < 0:
            raise ValueError("best_distance_m must not be negative")

        self._path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self._path.parent,
            prefix=f"{self._path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(
                    {"version": RECORD_VERSION, "best_distance_m": best_distance_m},
                    handle,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self._path)
        finally:
            temporary_path.unlink(missing_ok=True)
