"""tools/generate_checksums.py takes no arguments (session 4e2).

Before 4e2 it ignored every argument, so `--help` rewrote checksums.json.
Now `--help` prints help and an unknown argument exits non-zero; in both
cases nothing is written. The checks run the script as a subprocess against
the real checksums.json and compare its bytes before and after.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "generate_checksums.py"
MANIFEST = ROOT / "checksums.json"


def _run(*args):
    before = MANIFEST.read_bytes()
    proc = subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=ROOT)
    assert MANIFEST.read_bytes() == before, "checksums.json changed"
    return proc


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_prints_and_writes_nothing(flag):
    proc = _run(flag)
    assert proc.returncode == 0
    assert "usage:" in proc.stdout
    assert "wrote" not in proc.stdout


@pytest.mark.parametrize("args", [["--check"], ["--bogus"], ["extra"], ["--help-me"]])
def test_unknown_arguments_exit_nonzero_and_write_nothing(args):
    proc = _run(*args)
    assert proc.returncode != 0
    assert "unrecognized arguments" in proc.stderr or "error:" in proc.stderr
    assert "wrote" not in proc.stdout
