"""Shared pytest fixtures for the test suite."""
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def fixture_as_test(tmp_path):
    """Copy a fixture from tests/fixtures/ to a temp dir named TEST.json.

    Fixtures are named after what they test (invalid_duplicate_dates.json),
    but they carry code: "TEST". The validator's code==filename rule would
    fire before the intended check. Copying to TEST.json satisfies the
    filename rule so the intended error surfaces.
    """
    def _copy(fixture_name):
        src = Path(__file__).parent / "fixtures" / fixture_name
        assert src.exists(), f"fixture not found: {src}"
        dst = tmp_path / "TEST.json"
        shutil.copy(src, dst)
        return dst
    return _copy
