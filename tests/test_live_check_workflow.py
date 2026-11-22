"""The weekly live check workflow and the actions every workflow uses (4b3)."""
import glob
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_tier_coverage as tc  # noqa: E402

WF = ROOT / ".github" / "workflows"
LIVE_TEXT = (WF / "live-fetcher-check.yml").read_text(encoding="utf-8")
LIVE = yaml.safe_load(LIVE_TEXT)


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


def test_tier_guard_fails_on_no_tier_and_on_two_tiers(monkeypatch, tmp_path, capsys):
    # 4b4: both were warnings (XBUL, XIST and XSWX sat in no tier).
    two = "  TIER1_MICS: 'XNYS,XLON'\n  TIER9_MICS_BUILT: 'XLON'\n"
    assert tc.duplicates(two) == ["XLON"]
    wf = tmp_path / "wf.yml"
    wf.write_text("env:\n  TIER1_MICS: 'XNYS'\n")
    monkeypatch.setattr(tc, "WORKFLOW", wf)
    assert tc.main([]) == 1  # every other registered fetcher is in no tier
    assert "Registered but listed in no tier" in capsys.readouterr().out
    wf.write_text(LIVE_TEXT.replace("TIER9_MICS_BUILT: 'XIST,XSWX,XBUL'", "TIER9_MICS_BUILT: 'XIST,XSWX,XBUL,XNYS'"))
    assert tc.main([]) == 1
    assert "more than one tier: ['XNYS']" in capsys.readouterr().out


def test_xbul_xist_xswx_are_placed_once():
    lists = tc.tier_lists(LIVE_TEXT)
    for mic in ("XBUL", "XIST", "XSWX"):
        assert sum(t.count(mic) for t in lists) == 1, mic
    stable_exclude = LIVE["jobs"]["live-check-stable"]["env"]["STABLE_EXCLUDE"].split(",")
    assert "XIST" not in stable_exclude  # a stable implemented fetcher
    assert {"XSWX", "XBUL"} <= set(stable_exclude)
