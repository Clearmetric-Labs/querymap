"""Dev wiki generation tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_build_parser_importable() -> None:
    from clearmetric.cli import build_parser

    parser = build_parser()
    assert parser.prog == "cm"


def test_wiki_reference_docs_exist() -> None:
    assert (REPO / "docs" / "reference" / "contract.md").is_file()
    assert (REPO / "docs" / "reference" / "lineage-limitations.md").is_file()


def test_generate_wiki_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_wiki.py", "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
