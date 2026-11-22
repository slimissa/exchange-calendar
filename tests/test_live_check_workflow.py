"""The weekly live check workflow and the actions every workflow uses (4b3)."""
import glob
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_tier_coverage as tc  # noqa: E402

WF = ROOT / ".github" / "workflows"
LIVE = yaml.safe_load((WF / "live-fetcher-check.yml").read_text(encoding="utf-8"))


def _steps(job):
    return LIVE["jobs"][job]["steps"]


def test_every_workflow_uses_node24_checkout_and_setup_python():
    for f in sorted(glob.glob(str(WF / "*.yml"))) + [str(WF / "publish.yml.disabled")]:
        text = Path(f).read_text(encoding="utf-8")
        assert "actions/checkout@v4" not in text and "actions/setup-python@v5" not in text, f


def test_stable_job_permissions_are_contents_read_and_issues_write():
    assert LIVE["jobs"]["live-check-stable"]["permissions"] == {"contents": "read", "issues": "write"}


def test_scheduled_run_escalates_through_the_issue():
    runs = "\n".join(s.get("run", "") for s in _steps("live-check-stable"))
    assert "--json-out live-results.json" in runs
    assert "tools/live_check_escalate.py" in runs
    assert 'gh issue create --title "$title" --label live-check' in runs
    assert "gh issue close" in runs and "exit 1" in runs
    assert "git push" not in runs and "git commit" not in runs  # no commits from CI


def test_manual_run_honours_the_mic_input():
    runs = "\n".join(s.get("run", "") for s in _steps("live-check-stable"))
    assert '--mic "${{ github.event.inputs.mic }}"' in runs


def test_coverage_guard_is_a_real_check_again():
    runs = "\n".join(s.get("run", "") for s in _steps("verify-coverage"))
    assert "tools/check_tier_coverage.py" in runs
    assert "existing guard script, unchanged" not in (WF / "live-fetcher-check.yml").read_text(encoding="utf-8")


def test_tier_coverage_rules():
    text = "env:\n  TIER1_MICS: 'XNYS,XLON'\n  TIER2_MICS_BUILT: 'XMAD'\n"
    assert tc.tier_mics(text) == {"XNYS", "XLON", "XMAD"}
    assert tc.blocked_mics("# Blocked\n## XKUW — WAF\n## XSAU\n") == {"XKUW", "XSAU"}
    missing, unexpected = tc.check({"XNYS", "XMAD", "XKUW"}, {"XNYS", "XBUL"}, {"XKUW"})
    assert missing == ["XMAD"] and unexpected == ["XBUL"]


def test_tier_coverage_passes_on_the_tree():
    assert tc.main([]) == 0
