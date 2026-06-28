from __future__ import annotations

import subprocess
import sys


def test_connect_help_lists_warehouse_not_snowflake():
    result = subprocess.run(
        [sys.executable, "-m", "clearmetric.cli", "connect", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    output = result.stdout.lower()
    assert "warehouse" in output
    assert "snowflake" not in output
