"""PyInstaller entry point for the standalone builds."""

from albatross.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
