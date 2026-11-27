"""scripts/release.sh in a throwaway git repo with a bare "origin" (4b7).

On 2026-11-24 `scripts/release.sh 2.34.0` ran on a tree already released as
v2.34.0. The precondition failed ("VERSION is already 2.34.0"), and the
failure trap, which decided from HEAD's subject and origin/main's contents,
reverted the existing release commit and pushed the revert. These tests run
the real script against a scratch repository: every tool it calls is a stub,
`gh` is a stub that reports a CI result, and `sleep` is a no-op, so nothing
reaches the network or GitHub.
"""
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

if shutil.which("jq") is None or shutil.which("git") is None:  # pragma: no cover
    pytest.skip("release.sh needs git and jq", allow_module_level=True)

RELEASE_FILES = [
    "exchange_calendar.sql", "exchange_calendar.postgresql.sql", "exchange_calendar.mysql.sql",
    "exchange_calendar.sqlite.sql", "exchange_calendar.exchanges.parquet",
    "exchange_calendar.sessions.parquet", "exchange_calendar.holidays.parquet",
    "exchange_calendar.ad_hoc_closures.parquet", "exchange_calendar.confidence.parquet",
]
STUB_TOOLS = [
    "check_country_codes.py", "check_doc_facts.py", "check_doc_links.py", "check_fetcher_freshness.py",
    "check_mic_codes.py", "check_mojibake.py", "check_release_claims.py", "check_snapshot_freshness.py",
    "check_stale_verifications.py", "check_stale_year_urls.py", "check_wrapper_snapshot.py",
    "derive_confidence.py", "export_parquet.py", "export_sql.py", "gen_readme_table.py",
    "migrate_sessions.py", "validate.py",
]
BUILD = '''import json
v = open("VERSION").read().strip()
json.dump({"meta": {"version": v}}, open("calendar.json", "w"))
'''


def git(cwd, *args, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise AssertionError(f"git {' '.join(args)}: {r.stderr}")
    return r.stdout.strip()


def write(path, text, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mode:
        path.chmod(path.stat().st_mode | mode)


def changelog(*versions):
    body = "# Changelog\n\n"
    for v in versions:
        body += f"## [{v}] - 2026-11-24\n\n- entry\n\n"
    return body


@pytest.fixture
def repo(tmp_path):
    """A releasable scratch repo at 1.0.0 with CHANGELOG [1.1.0] ready, pushed to a bare origin."""
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    bin_ = tmp_path / "bin"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "init", "-q", "-b", "main", str(work))
    for k, v in (("user.name", "release-test"), ("user.email", "release-test@localhost")):
        git(work, "config", k, v)
    (work / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "release.sh", work / "scripts" / "release.sh")
    shutil.copytree(ROOT / ".github" / "workflows", work / ".github" / "workflows")
    (work / "tools").mkdir()
    shutil.copy(ROOT / "tools" / "check_changelog_order.py", work / "tools" / "check_changelog_order.py")
    # 4b11.1: release.sh runs the shared gate file.
    shutil.copy(ROOT / "tools" / "local_gate.sh", work / "tools" / "local_gate.sh")
    for name in STUB_TOOLS:
        write(work / "tools" / name, "pass\n")
    write(work / "tools" / "build.py", BUILD)
    write(work / "tools" / "check_cross_language.sh", "exit 0\n")
    write(work / "tools" / "release_claims.json", json.dumps({"1.1.0": []}) + "\n")
    write(work / ".gitignore", "__pycache__/\n.pytest_cache/\n")
    write(work / "VERSION", "1.0.0\n")
    write(work / "README.md", "![registry](https://img.shields.io/badge/registry-1.0.0-orange)\n"
                              "automated fetchers as of v1.0.0\n")
    write(work / "CHANGELOG.md", changelog("1.1.0", "1.0.0"))
    write(work / "calendar.json", json.dumps({"meta": {"version": "1.0.0"}}))
    write(work / "wrappers" / "python" / "exchange_calendar" / "calendar.json", "{}")
    for d in ("javascript", "go", "rust"):
        (work / "wrappers" / d).mkdir(parents=True, exist_ok=True)
        write(work / "wrappers" / d / ".keep", "")
    for f in RELEASE_FILES:
        write(work / f, "x\n")
    write(work / "tests" / "test_ok.py", "def test_ok():\n    pass\n")
    write(work / "Makefile", "package:\n\tcp calendar.json wrappers/python/exchange_calendar/calendar.json\n")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "init")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    git(work, "branch", "-q", "--set-upstream-to=origin/main", "main")
    # PATH stubs: no network, no real CI, no waiting.
    for name in ("npm", "go", "cargo"):
        write(bin_ / name, "#!/bin/sh\nexit 0\n", stat.S_IEXEC)
    write(bin_ / "sleep", "#!/bin/sh\nexit 0\n", stat.S_IEXEC)
    write(bin_ / "gh", '#!/bin/sh\ncat "$GH_STUB_JSON"\n', stat.S_IEXEC)
    write(tmp_path / "ci.json", '[{"status": "completed", "conclusion": "success", "databaseId": 1}]')
    return {"work": work, "origin": origin, "bin": bin_, "ci": tmp_path / "ci.json"}


def release(r, version, ci="success", dry=False):
    r["ci"].write_text(json.dumps([{"status": "completed", "conclusion": ci, "databaseId": 7}]))
    env = dict(os.environ, PATH=f"{r['bin']}:{os.environ['PATH']}", GH_STUB_JSON=str(r["ci"]),
               POLL_TIMEOUT="5", DRY_RUN="1" if dry else "0")
    env.pop("GIT_DIR", None)
    return subprocess.run(["bash", "scripts/release.sh", version], cwd=r["work"], env=env,
                          capture_output=True, text=True, timeout=300)


def snapshot(r):
    return {
        "head": git(r["work"], "rev-parse", "HEAD"),
        "origin": git(r["origin"], "rev-parse", "main"),
        "log": git(r["origin"], "log", "--format=%s", "main"),
        "status": git(r["work"], "status", "--porcelain"),
        "version": (r["work"] / "VERSION").read_text().strip(),
    }


def test_a_normal_release_succeeds(repo):
    """Harness sanity: 1.0.0 -> 1.1.0 commits, pushes, polls the stub CI and tags."""
    p = release(repo, "1.1.0")
    assert p.returncode == 0, p.stdout + p.stderr
    s = snapshot(repo)
    assert s["log"].splitlines()[0] == "Release v1.1.0" and s["version"] == "1.1.0"
    assert git(repo["origin"], "tag", "--list") == "v1.1.0"


def test_rerun_on_a_released_tree_reverts_nothing(repo):
    """(1) The 2026-11-24 incident: release again a version that is already
    released. Run twice: once with the tag in place, once with the tag gone
    (so only "VERSION is already" stops it). Neither run may touch history."""
    assert release(repo, "1.1.0").returncode == 0
    before = snapshot(repo)
    p = release(repo, "1.1.0")
    assert p.returncode != 0
    assert "VERSION is already 1.1.0" in p.stderr
    assert "reverting" not in p.stderr and "history untouched" in p.stderr
    assert snapshot(repo) == before
    # Without the tag: the old trap reverted here (HEAD "Release v1.1.0", on origin/main).
    git(repo["work"], "tag", "-d", "v1.1.0")
    git(repo["work"], "push", "-q", "origin", ":refs/tags/v1.1.0")
    before = snapshot(repo)
    p = release(repo, "1.1.0")
    assert p.returncode != 0 and "reverting" not in p.stderr
    assert snapshot(repo) == before
    assert "Revert" not in before["log"]


def test_existing_tag_stops_before_any_change(repo):
    """(2) A tag v1.1.0 on origin only (not local, VERSION still 1.0.0) stops
    the run before the version bump; a local-only tag does too."""
    git(repo["work"], "tag", "v1.1.0")
    git(repo["work"], "push", "-q", "origin", "v1.1.0")
    git(repo["work"], "tag", "-d", "v1.1.0")
    before = snapshot(repo)
    p = release(repo, "1.1.0")
    assert p.returncode != 0
    assert "tag v1.1.0 already exists on origin" in p.stderr
    assert "Bumping version sites" not in p.stdout
    assert snapshot(repo) == before and before["version"] == "1.0.0"
    git(repo["work"], "push", "-q", "origin", ":refs/tags/v1.1.0")
    git(repo["work"], "tag", "v1.1.0")
    p = release(repo, "1.1.0")
    assert p.returncode != 0 and "tag v1.1.0 already exists locally" in p.stderr
    assert snapshot(repo) == before


def test_failure_after_own_commit_and_push_reverts_it(repo):
    """(3) CI fails on the release commit this run pushed: the trap reverts
    that commit on origin and no tag is made."""
    before = snapshot(repo)
    p = release(repo, "1.1.0", ci="failure")
    assert p.returncode != 0
    assert "this run pushed release commit" in p.stderr and "reverting it" in p.stderr
    log = git(repo["origin"], "log", "--format=%s", "main").splitlines()
    assert log[:3] == ['Revert "Release v1.1.0"', "Release v1.1.0", "init"]
    assert git(repo["origin"], "tag", "--list") == ""
    assert (repo["work"] / "VERSION").read_text().strip() == "1.0.0" == before["version"]
    assert git(repo["work"], "status", "--porcelain") == ""


def test_failure_before_the_commit_restores_files_only(repo):
    """A gate failure after the bump but before the commit restores the version
    sites and leaves history alone."""
    write(repo["work"] / "tools" / "validate.py", "raise SystemExit(3)\n")
    git(repo["work"], "commit", "-q", "-am", "make validate fail")
    git(repo["work"], "push", "-q", "origin", "main")
    before = snapshot(repo)
    p = release(repo, "1.1.0")
    assert p.returncode != 0
    assert "Restored version sites and artifacts on failure" in p.stderr
    assert snapshot(repo) == before



def test_release_runs_the_shared_local_gate():
    """4b11.1: one gate. release.sh calls tools/local_gate.sh and keeps no
    inline copy of its commands; CI's validate.yml runs the same file."""
    release_sh = (ROOT / "scripts" / "release.sh").read_text(encoding="utf-8")
    gate = (ROOT / "tools" / "local_gate.sh").read_text(encoding="utf-8")
    assert 'bash tools/local_gate.sh "$VERSION"' in release_sh
    for line in gate.splitlines():
        if line.strip().startswith("run "):
            assert line.strip() not in release_sh, line
    assert "run python3 tools/migrate_sessions.py --check --quiet" in gate
    assert "bash tools/local_gate.sh" in (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")



def test_dry_run_runs_the_gate_and_changes_nothing(repo):
    """4b12: a dry run executes the read-only checks (the gate's stub tools
    run and leave a mark) and changes neither the tree nor origin."""
    write(repo["work"] / "tools" / "migrate_sessions.py",
          "open('gate-ran.marker', 'w').write('x')\n")
    write(repo["work"] / ".gitignore", "__pycache__/\n.pytest_cache/\ngate-ran.marker\n")
    git(repo["work"], "commit", "-q", "-am", "mark gate runs")
    git(repo["work"], "push", "-q", "origin", "main")
    before = snapshot(repo)
    p = release(repo, "1.1.0", dry=True)
    assert p.returncode == 0, p.stderr
    assert (repo["work"] / "gate-ran.marker").exists()
    assert "DRY RUN — stopping before commit" in p.stdout
    assert snapshot(repo) == before


def test_failing_gate_check_fails_a_dry_run(repo):
    """4b12: before, DRY_RUN=1 only printed the gate, so a failing check
    passed a dry run (4b11: migrate_sessions --check). Now it fails it, and
    nothing changes."""
    write(repo["work"] / "tools" / "migrate_sessions.py", "raise SystemExit(4)\n")
    git(repo["work"], "commit", "-q", "-am", "make migrate_sessions fail")
    git(repo["work"], "push", "-q", "origin", "main")
    before = snapshot(repo)
    p = release(repo, "1.1.0", dry=True)
    assert p.returncode != 0
    assert "DRY RUN — stopping before commit" not in p.stdout
    assert "nothing to restore" in p.stderr
    assert snapshot(repo) == before


def test_failing_changelog_order_fails_a_dry_run(repo):
    """4b12: the CHANGELOG order check runs in a dry run (it was printed only)."""
    write(repo["work"] / "CHANGELOG.md", changelog("1.0.0", "1.1.0"))
    git(repo["work"], "commit", "-q", "-am", "break the order")
    git(repo["work"], "push", "-q", "origin", "main")
    p = release(repo, "1.1.0", dry=True)
    assert p.returncode != 0
    assert "DRY RUN — stopping before commit" not in p.stdout
