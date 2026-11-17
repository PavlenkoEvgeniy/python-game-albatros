"""Command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from albatross import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="albatross",
        description="A calm arcade game about an albatross gliding from a mountain.",
    )
    parser.add_argument("--version", action="store_true", help="print the version and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"albatross {__version__}")
        return 0

    from albatross.application.app import GameApp

    GameApp.create().run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
