#!/usr/bin/env python3
"""
test_divergence_workflow.py — pins the weekly divergence CI job.

Run:
    python3 -m pytest tests/test_divergence_workflow.py -v
"""

from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
WORKFLOW = REPO / ".github" / "workflows" / "divergence.yml"


@pytest.fixture(scope="module")
def text():
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parsed(text):
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load(text)


def test_runs_weekly_on_monday_0800_utc_and_on_demand(parsed):
    triggers = parsed.get("on", parsed.get(True))
    assert triggers["schedule"] == [{"cron": "0 8 * * 1"}]
    assert "workflow_dispatch" in triggers


def test_job_setup(parsed):
    job = parsed["jobs"]["divergence"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["permissions"] == {"contents": "write", "pull-requests": "write"}


def test_steps_in_order(text):
    order = [
        "actions/checkout@v4",
        "python-version: '3.11'",
        "pip install -r requirements.txt",
        "pip install -r requirements-dev.txt",
        "python3 tools/divergence_test.py --exchanges all --year 2024-2026",
        "python3 tools/divergence_report.py",
        "peter-evans/create-pull-request@v6",
    ]
    positions = [text.index(item) for item in order]
    assert positions == sorted(positions)


def test_pull_request_settings(text):
    assert "branch: automated/divergence-report" in text
    assert "docs/DIVERGENCE.md" in text
    assert "docs/divergence_triage.json" in text
    assert "📊 Weekly divergence report" in text
    assert ("Automated divergence check against pandas_market_calendars "
            "and exchange_calendars.") in text


def test_readme_has_badge():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "actions/workflows/divergence.yml/badge.svg" in readme


def test_report_header_says_ci_regenerates_it():
    header = (REPO / "docs" / "DIVERGENCE.md").read_text(encoding="utf-8")[:1500]
    assert "regenerated automatically every Monday" in header
    assert "Manual edits will be overwritten" in header
