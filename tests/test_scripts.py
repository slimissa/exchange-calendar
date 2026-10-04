

# ── v2.10.1: release trap recovery ──────────────────────────────────

import subprocess
from pathlib import Path
import pytest


def _git(args, cwd, check=True):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=check,
        capture_output=True, text=True,
    )


def _init_repo(tmp_path):
    """Create a minimal git repo mimicking the release-script layout."""
    _git(["init", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@t.t"], tmp_path)
    _git(["config", "user.name", "T"], tmp_path)
    (tmp_path / "VERSION").write_text("1.0.0\n")
    (tmp_path / "README.md").write_text("registry-1.0.0-orange\n")
    (tmp_path / "CHANGELOG.md").write_text("## [1.0.0] — 2026-01-01\n")
    (tmp_path / "calendar.json").write_text('{"meta": {"version": "1.0.0"}}\n')
    _git(["add", "."], tmp_path)
    _git(["commit", "-m", "Initial"], tmp_path)


def _is_release_commit(repo):
    r = _git(["log", "-1", "--format=%s"], repo, check=False)
    return r.stdout.strip().startswith("Release v")


def test_trap_detects_pre_commit_failure(tmp_path):
    """If HEAD is not a release commit, is_release_commit() is False."""
    _init_repo(tmp_path)
    assert _is_release_commit(tmp_path) is False


def test_trap_detects_post_commit_failure(tmp_path):
    """After the release commit is created, is_release_commit() is True."""
    _init_repo(tmp_path)
    (tmp_path / "VERSION").write_text("1.0.1\n")
    _git(["add", "VERSION"], tmp_path)
    _git(["commit", "-m", "Release v1.0.1"], tmp_path)
    assert _is_release_commit(tmp_path) is True


def test_trap_restores_files_pre_commit(tmp_path):
    """Pre-commit failure: restore files from HEAD."""
    _init_repo(tmp_path)
    (tmp_path / "VERSION").write_text("1.0.1\n")
    (tmp_path / "README.md").write_text("registry-1.0.1-orange\n")

    # Simulate the restore
    for f in ["VERSION", "README.md"]:
        _git(["checkout", "HEAD", "--", f], tmp_path)

    assert (tmp_path / "VERSION").read_text().strip() == "1.0.0"
    assert "1.0.1" not in (tmp_path / "README.md").read_text()


def test_trap_reverts_post_push_failure(tmp_path):
    """Post-push failure: revert the release commit."""
    _init_repo(tmp_path)
    (tmp_path / "VERSION").write_text("1.0.1\n")
    _git(["add", "VERSION"], tmp_path)
    _git(["commit", "-m", "Release v1.0.1"], tmp_path)

    # Simulate the recovery: revert
    _git(["revert", "HEAD", "--no-edit"], tmp_path)

    assert (tmp_path / "VERSION").read_text().strip() == "1.0.0"
    log = _git(["log", "--oneline"], tmp_path).stdout
    assert "Revert" in log
