"""tools/check_verification.py: the coverage-span checks added in Phase 4d.

Check 5 of the tool (see its docstring): coverage spans tile generation_range
exactly, a span's source label does not contradict the data it covers, and
contradicted_by / unconfirmed dates lie inside their span. The unit tests use
synthetic exchanges; the tree tests run the tool on a temporary copy of the
real inputs, which are only read.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_verification as cv  # noqa: E402

LIBS = ("exchange_calendars", "pandas_market_calendars")
NO_END = {"exchange_calendars": {}, "pandas_market_calendars": {}}



def _ex(spans, gr=("2010-01-01", "2029-12-31"), cov_from=None, cov_to=None,
        explicit=(), ad_hoc=()):
    return {
        "code": "XTST",
        "generation_range": list(gr),
        "holidays": {"explicit": list(explicit)},
        "ad_hoc_closures": list(ad_hoc),
        "verification": {"coverage": {
            "from": cov_from or gr[0], "to": cov_to or gr[1], "sources": spans}},
    }


def _span(a, b, source="exchange_calendars", **extra):
    return {"from": a, "to": b, "source": source, **extra}


GOOD = [
    _span("2010-01-01", "2024-12-31", sampled=None),
    _span("2025-01-01", "2026-12-31", "exchange_calendars + exchange_publications"),
    _span("2027-01-01", "2029-12-31", "exchange_calendars + standing holiday pattern"),
]


def _problems(ex, libs=LIBS, end=NO_END, unpublished=()):
    return cv.coverage_problems(ex, libs, end, set(unpublished))


# --- 5a: tiling ------------------------------------------------------------

def test_consistent_coverage_has_no_problem():
    assert _problems(_ex(GOOD)) == []


def test_no_coverage_is_not_checked():
    assert cv.coverage_problems({"code": "XTST", "verification": {}}, LIBS, NO_END, set()) == []


def test_gap_between_spans():
    spans = [GOOD[0], _span("2025-02-01", "2029-12-31", "exchange_calendars + x pattern")]
    out = _problems(_ex(spans))
    assert len(out) == 1 and "gap 2025-01-01..2025-01-31" in out[0]


def test_overlap_between_spans():
    spans = [GOOD[0], _span("2024-06-01", "2029-12-31", "exchange_calendars + x pattern")]
    out = _problems(_ex(spans))
    assert len(out) == 1 and "overlaps" in out[0]


def test_span_outside_range_and_coverage_to_past_range_end():
    out = _problems(_ex(GOOD, gr=("2010-01-01", "2029-09-23"), cov_to="2029-12-31"))
    assert any("coverage.to 2029-12-31" in p for p in out)
    assert any("2027-01-01..2029-12-31 lies outside" in p for p in out)


def test_coverage_from_earlier_than_range_start_fails():
    out = _problems(_ex(GOOD, gr=("2011-01-01", "2029-12-31"), cov_from="2010-01-01"))
    assert len(out) == 2
    assert any("coverage.from 2010-01-01" in p for p in out)
    assert any("2010-01-01..2024-12-31 lies outside" in p for p in out)


def test_spans_stopping_short_of_range_end_leave_a_gap():
    out = _problems(_ex(GOOD[:2], cov_to="2029-12-31"))
    assert any("gap 2027-01-01..2029-12-31 after the last span" in p for p in out)


def test_span_beyond_range_end():
    spans = GOOD + [_span("2030-01-01", "2031-12-31", "not covered")]
    out = _problems(_ex(spans))
    assert len(out) == 1 and "2030-01-01..2031-12-31 lies outside" in out[0]


# --- 5b: labels against data ----------------------------------------------

def test_predicted_entry_in_publication_span():
    ex = _ex(GOOD, explicit=[{"date": "2026-12-24", "predicted": True}])
    out = _problems(ex)
    assert len(out) == 1 and "1 predicted entry (2026-12-24)" in out[0]


def test_predicted_ad_hoc_closure_counts_too():
    ex = _ex(GOOD, ad_hoc=[{"date": "2025-03-03", "predicted": True}])
    assert len(_problems(ex)) == 1


def test_predicted_entry_in_pattern_span_is_fine():
    ex = _ex(GOOD, explicit=[{"date": "2028-12-24", "predicted": True}])
    assert _problems(ex) == []


def test_unpublished_triage_date_in_publication_span():
    out = _problems(_ex(GOOD), unpublished={"2026-03-10"})
    assert len(out) == 1 and "triaged unpublished (2026-03-10)" in out[0]


def _doubt_span(**over):
    s = GOOD[1] | {"unconfirmed": ["2026-12-24"], "recheck_date": "2026-12-22",
                   "source": "exchange_calendars + exchange_publications; "
                             "2026-12-24 early close unconfirmed"}
    s.update(over)
    return [GOOD[0], s, GOOD[2]]


def test_unconfirmed_date_with_recheck_and_honest_label_is_fine():
    ex = _ex(_doubt_span(), explicit=[{"date": "2026-12-24", "predicted": True}])
    assert _problems(ex) == []
    assert _problems(_ex(_doubt_span()), unpublished={"2026-12-24"}) == []


def test_unconfirmed_needs_a_recheck_date():
    spans = _doubt_span()
    del spans[1]["recheck_date"]
    assert len(_problems(_ex(spans), unpublished={"2026-12-24"})) == 1


def test_unconfirmed_needs_a_label_that_says_so():
    spans = _doubt_span(source="exchange_calendars + exchange_publications")
    ex = _ex(spans, explicit=[{"date": "2026-12-24", "predicted": True}])
    assert len(_problems(ex)) == 1


def test_unconfirmed_covers_only_the_dates_it_lists():
    ex = _ex(_doubt_span(), explicit=[{"date": "2026-12-24", "predicted": True},
                                      {"date": "2026-12-31", "predicted": True}])
    out = _problems(ex)
    assert len(out) == 1 and "(2026-12-31)" in out[0]


def test_not_covered_span_may_hold_predictions():
    spans = GOOD[:2] + [_span("2027-01-01", "2029-12-31",
                              "not covered (exchange_calendars stops at 2026)")]
    ex = _ex(spans, explicit=[{"date": "2028-01-03", "predicted": True}])
    assert _problems(ex, end={"exchange_calendars": {"XTST": 2026},
                              "pandas_market_calendars": {}},
                     unpublished={"2028-01-26"}) == []


def test_library_named_without_data():
    out = _problems(_ex(GOOD), libs=("pandas_market_calendars",))
    assert len(out) == 3 and all("has no data for XTST" in p for p in out)


def test_library_named_past_its_last_year():
    out = _problems(_ex(GOOD), end={"exchange_calendars": {"XTST": 2026},
                                    "pandas_market_calendars": {}})
    assert len(out) == 1 and "2027-01-01..2029-12-31 names exchange_calendars" in out[0]


def test_library_end_years_are_read_from_the_report():
    text = (ROOT / "docs" / "DIVERGENCE.md").read_text(encoding="utf-8")
    ends = cv.library_end_years(text)
    assert ends["exchange_calendars"] == {"XBOM": 2026, "XSES": 2026, "XSHG": 2026}


# --- 5c: dates inside their span ------------------------------------------

def test_contradicted_by_outside_span():
    spans = [GOOD[0] | {"contradicted_by": ["2025-05-01"]}] + GOOD[1:]
    out = _problems(_ex(spans))
    assert len(out) == 1 and "contradicted_by 2025-05-01 lies outside" in out[0]


def test_unconfirmed_outside_span():
    spans = GOOD[:1] + [GOOD[1] | {"unconfirmed": ["2024-12-31"]}] + GOOD[2:]
    out = _problems(_ex(spans))
    assert len(out) == 1 and "unconfirmed 2024-12-31 lies outside" in out[0]


def test_dates_inside_span_are_fine():
    spans = [GOOD[0] | {"contradicted_by": ["2013-11-14"], "unconfirmed": ["2010-01-01"]}] + GOOD[1:]
    assert _problems(_ex(spans)) == []


# --- the tool on the real tree --------------------------------------------

def _tree(tmp_path):
    shutil.copytree(ROOT / "exchanges", tmp_path / "exchanges")
    (tmp_path / "docs").mkdir()
    for name in ("DIVERGENCE.md", "divergence_triage.json"):
        shutil.copy(ROOT / "docs" / name, tmp_path / "docs" / name)
    return tmp_path


def test_real_tree_classes_and_dates_are_consistent():
    """Checks 1-4 block. Until Phase 4d no CI step or test ran this tool, which is
    how a last_checked split (70 files at one date, 4 at another) reached v2.28.0."""
    problems, _, _ = cv.check(ROOT)
    assert problems == []


def test_real_tree_has_no_coverage_finding():
    """Check 5 blocks since 4d.1, when the last of the 15 Phase 4d findings
    was resolved."""
    _, _, coverage = cv.check(ROOT)
    assert coverage == []


def test_coverage_findings_fail_the_tool(tmp_path, capsys):
    root = _tree(tmp_path)
    path = root / "exchanges" / "XTSE.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    gr = data["generation_range"]
    data["verification"]["coverage"] = {
        "from": gr[0], "to": gr[1],
        "sources": [{"from": gr[0], "to": "2020-12-31", "source": "exchange_calendars"}]}
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    assert cv.main(["--root", str(root)]) == 1
    assert "coverage: XTSE: gap 2021-01-01" in capsys.readouterr().out
    assert cv.main(["--root", str(root), "--strict-coverage"]) == 1
    assert cv.main(["--root", str(ROOT)]) == 0
