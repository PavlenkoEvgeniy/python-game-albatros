"""Best-result rules."""

from __future__ import annotations


def updated_best(best_distance_m: int | None, candidate_m: int) -> int:
    """Return the best distance after a finished run.

    The first finished run always becomes the record; later runs only replace it
    when they are strictly better.
    """
    if best_distance_m is None or candidate_m > best_distance_m:
        return candidate_m
    return best_distance_m
