from __future__ import annotations

import pytest

from albatross import __version__
from albatross.__main__ import build_parser, main


def test_version_flag_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"albatross {__version__}"


def test_help_exits_without_opening_a_window() -> None:
    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(["--help"])
    assert excinfo.value.code == 0
