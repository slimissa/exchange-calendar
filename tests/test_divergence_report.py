#!/usr/bin/env python3
"""
test_divergence_report.py — Tests for tools/divergence_report.py.

Checks that the report generator:
    1. Renders the summary table with the Exchange | Registry | PMC | EC |
       Disagreements columns
    2. Shows "No reference data" for a library that does not know an exchange
       and lists that exchange in its own section
    3. Lists every disagreeing date with what each source says
    4. Computes agreement as agreed trading days / (agreed + disagreeing)
    5. Is deterministic and exits 2 on an unreadable input
    6. Annotates still-disagreeing dates with a hand-checked triage verdict and
       lists the triage entries, and rejects an unknown verdict

Run:
    python3 -m pytest tests/test_divergence_report.py -v
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import divergence_report as dr  # noqa: E402

REG, PMC, EC = "registry", "pandas_market_calendars", "exchange_calendars"
NO_REF = "No reference data: RuntimeError: unknown"


def _year(totals, agree, disagreements=(), unavailable=None, mirror=True):
    return {
        "total_trading_days": totals,
        "sources_compared": sorted(k for k, v in totals.items() if isinstance(v, int)),
        "sources_unavailable": unavailable or {},
        "all_agree_trading_days": [],
        "all_agree_closed_weekdays": [],
        "disagreements": list(disagreements),
        "summary": {"agree_trading": agree, "agree_closed_weekdays": 0,
                    "disagreements": len(disagreements)},
        "pmc_mirrors_exchange_calendars": mirror,
    }


def _report():
    diff = {"date": "2026-04-24", "weekday": "Fri",
            "says": {REG: "closed", PMC: "open", EC: "open"}}
    return {
        "years": [2024, 2026],
        "libraries": {"exchange_calendars": "1.0", "pandas_market_calendars": "2.0"},
        "exchanges": {
            "XAAA": {"years": {
                "2024": _year({REG: "No registry data: out of range", PMC: 250, EC: 250},
                              250, unavailable={REG: "No registry data: out of range"}),
                "2026": _year({REG: 251, PMC: 253, EC: 253}, 251, [diff]),
            }},
            "XBBB": {"years": {
                "2024": _year({REG: "No registry data: x", PMC: NO_REF, EC: NO_REF}, 0,
                              unavailable={REG: "No registry data: x", PMC: NO_REF, EC: NO_REF},
                              mirror=None),
                "2026": _year({REG: 252, PMC: NO_REF, EC: NO_REF}, 0,
                              unavailable={PMC: NO_REF, EC: NO_REF}, mirror=None),
            }},
        },
    }


class TestRender:
    def test_summary_table_header_and_rows(self):
        text = dr.render(_report())
        assert "| Exchange | Registry | PMC | EC | Disagreements | Agreement |" in text
        assert "| XAAA | 251 | 253 | 253 | 1 | 99.6% |" in text

    def test_missing_library_is_labelled_and_listed(self):
        text = dr.render(_report())
        assert "| XBBB | 252 | No reference data | No reference data | n/a | n/a |" in text
        assert "Neither library (1): XBBB" in text

    def test_disagreement_dates_are_listed_with_each_source(self):
        text = dr.render(_report())
        assert "### XAAA (1)" in text
        assert "registry closed, PMC open, EC open (1): 2026-04-24 Fr" in text

    def test_agreement_rate_ignores_agreed_closed_days(self):
        rows = {r["code"]: r for r in
                (dr.summarise(c, e) for c, e in _report()["exchanges"].items())}
        assert rows["XAAA"]["agree"] == 251 and rows["XAAA"]["disagreements"] == 1
        assert abs(rows["XAAA"]["rate"] - 251 / 252) < 1e-9
        assert rows["XBBB"]["rate"] is None

    def test_registry_scope_excludes_years_without_registry_data(self):
        row = dr.summarise("XAAA", _report()["exchanges"]["XAAA"])
        assert row["years"] == ["2026"]
        assert row["totals"][REG] == 251

    def test_mirror_note_counts_mirrored_exchanges(self):
        text = dr.render(_report())
        assert "PMC serves 1 of the exchanges" in text

    def test_libraries_only_section_for_years_without_registry(self):
        text = dr.render(_report())
        assert "## Libraries only" in text
        assert "No disagreement between the two libraries." in text

    def test_output_is_deterministic_and_ascii(self):
        a, b = dr.render(_report()), dr.render(_report())
        assert a == b
        assert a.isascii()


class TestMain:
    def test_writes_file(self, tmp_path):
        src, dst = tmp_path / "in.json", tmp_path / "out.md"
        src.write_text(json.dumps(_report()))
        assert dr.main(["--input", str(src), "--output", str(dst)]) == 0
        assert dst.read_text().startswith("# Divergence report")

    def test_missing_input_exits_2(self, tmp_path):
        assert dr.main(["--input", str(tmp_path / "nope.json"),
                        "--output", str(tmp_path / "o.md")]) == 2

    def test_non_report_input_exits_2(self, tmp_path):
        src = tmp_path / "in.json"
        src.write_text(json.dumps({"hello": 1}))
        assert dr.main(["--input", str(src), "--output", str(tmp_path / "o.md")]) == 2


def _triage():
    return {"entries": [
        {"exchange": "XAAA", "verdict": "library_error", "status": "registry_verified",
         "dates": ["2026-04-24"], "summary": "The exchange lists it as closed.",
         "source_url": "https://example.com/calendar"},
        {"exchange": "XCCC", "verdict": "registry_error", "status": "fixed",
         "fixed_in": "9.9.9", "dates": ["2026-01-02", "2026-01-03"],
         "summary": "Was missing.", "source_url": "https://example.com/other"},
    ]}


class TestTriage:
    def test_disagreeing_date_is_annotated_with_verdict(self):
        text = dr.render(_report(), _triage())
        assert "2026-04-24 Fr [library error]" in text

    def test_untriaged_date_has_no_tag(self):
        text = dr.render(_report())
        assert "2026-04-24 Fr" in text and "[library error]" not in text

    def test_triage_section_lists_entries_and_counts(self):
        text = dr.render(_report(), _triage())
        assert "## Triage" in text
        assert "Library error: 1 dates; Registry error: 2 dates." in text
        assert "### XAAA: Library error (1, registry verified, no change)" in text
        assert "### XCCC: Registry error (2, fixed in 9.9.9)" in text
        assert "Source: https://example.com/calendar" in text

    def test_no_triage_section_without_entries(self):
        assert "## Triage" not in dr.render(_report(), {"entries": []})

    def test_main_reads_triage_file(self, tmp_path):
        import json as _json
        src, tri, dst = tmp_path / "in.json", tmp_path / "t.json", tmp_path / "o.md"
        src.write_text(_json.dumps(_report()))
        tri.write_text(_json.dumps(_triage()))
        assert dr.main(["--input", str(src), "--triage", str(tri),
                        "--output", str(dst)]) == 0
        assert "[library error]" in dst.read_text()

    def test_unknown_verdict_exits_2(self, tmp_path):
        import json as _json
        src, tri = tmp_path / "in.json", tmp_path / "t.json"
        src.write_text(_json.dumps(_report()))
        bad = _triage()
        bad["entries"][0]["verdict"] = "whatever"
        tri.write_text(_json.dumps(bad))
        assert dr.main(["--input", str(src), "--triage", str(tri),
                        "--output", str(tmp_path / "o.md")]) == 2

    def test_missing_triage_file_is_fine(self, tmp_path):
        import json as _json
        src = tmp_path / "in.json"
        src.write_text(_json.dumps(_report()))
        assert dr.main(["--input", str(src), "--triage", str(tmp_path / "none.json"),
                        "--output", str(tmp_path / "o.md")]) == 0
