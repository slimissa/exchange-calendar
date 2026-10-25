#!/usr/bin/env python3
"""
test_check_doc_facts.py — Unit tests for check_doc_facts.py.

Tests that the prose-versus-facts gate:
    1. Passes when every claim matches docs/facts.json
    2. Fails (exit 1) on a wrong digit claim and a wrong word claim, and
       prints file, line, expected and actual
    3. Reads number words ("Seventy-four", "twenty", "four")
    4. Sums facts for combined claims (registered fetchers)
    5. Does not treat a bare "N exchanges" as a claim: "67 exchanges
       (includes UAE)" is the Saturday-Sunday count, not the total
    6. Skips fenced code blocks
    7. Exits 2 when facts.json is missing or malformed, a file is missing, or
       a scanned file contains no claim
    8. The real documents pass against the real docs/facts.json, and every
       default file carries at least one claim

Run:
    python3 -m pytest tests/test_check_doc_facts.py -v
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_doc_facts as cdf

FACTS = {
    "csv_tsv_files": 20, "exchanges_blocked_total": 30, "exchanges_no_fetcher": 28,
    "exchanges_total": 74, "fetchers_blocked": 2, "fetchers_ci_unreachable": 3,
    "fetchers_implemented": 41, "fetchers_registered": 46, "parquet_files": 5, "sql_files": 4,
}


def tree(tmp_path, readme, facts=FACTS):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "facts.json").write_text(json.dumps(facts))
    (tmp_path / "README.md").write_text(readme)
    return tmp_path


def run(root, capsys, *files):
    code = cdf.main(["--root", str(root), "--files", *(files or ("README.md",))])
    out = capsys.readouterr()
    return code, out.out, out.err


class TestNumberWords:
    @pytest.mark.parametrize("word,value", [("four", 4), ("twenty", 20), ("Seventy-four", 74),
                                             ("ninety-nine", 99), ("nineteen", 19), ("ZERO", 0), ("46", 46)])
    def test_to_int(self, word, value):
        assert cdf.to_int(word) == value


class TestMatching:
    def test_matching_claims_pass(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6 continents.\n46 have registered fetchers.\n")
        code, out, _ = run(root, capsys)
        assert code == 0 and "2 claim(s)" in out

    def test_wrong_digit_fails_with_location(self, tmp_path, capsys):
        root = tree(tmp_path, "Intro.\n\n75 exchanges across 6 continents.\n")
        code, out, _ = run(root, capsys)
        assert code == 1
        assert "README.md:3" in out and "says 75" in out and "has 74" in out

    def test_wrong_word_fails(self, tmp_path, capsys):
        root = tree(tmp_path, "Seventy-five exchanges. 46 have registered fetchers.\n")
        code, out, _ = run(root, capsys)
        assert code == 1 and "exchanges_total" in out

    def test_word_claim_passes(self, tmp_path, capsys):
        root = tree(tmp_path, "Seventy-four exchanges.\n")
        assert run(root, capsys)[0] == 0

    def test_summed_claim(self, tmp_path, capsys):
        wrong = dict(FACTS, fetchers_blocked=3)  # 41 + 3 + 3 = 47, README says 46
        root = tree(tmp_path, "46 have registered fetchers.\n", facts=wrong)
        code, out, _ = run(root, capsys)
        assert code == 1 and "has 47" in out

    def test_combined_ci_unreachable_and_blocked(self, tmp_path, capsys):
        root = tree(tmp_path, "5 documented as CI-unreachable (A, B, C) or blocked (D, E).\n")
        assert run(root, capsys)[0] == 0

    def test_every_wrong_claim_is_reported(self, tmp_path, capsys):
        root = tree(tmp_path, "99 exchanges across 6.\n1 have registered fetchers.\n")
        code, out, _ = run(root, capsys)
        assert code == 1 and "2 claim(s) disagree" in out

    def test_markdown_formatting_around_claim(self, tmp_path, capsys):
        root = tree(tmp_path, "**46 of 74 registry exchanges have automated fetchers** now.\n")
        assert run(root, capsys)[0] == 0

    def test_export_file_claims(self, tmp_path, capsys):
        text = ("four `exchange_calendar*.sql` files\n"
                "twenty `exchange_calendar.TABLE*.csv` and `.tsv` files\n"
                "five `exchange_calendar.TABLE.parquet` files\n")
        assert run(tree(tmp_path, text), capsys)[0] == 0
        assert run(tree(tmp_path, text.replace("four", "three")), capsys)[0] == 1


class TestVersion:
    def test_matching_version_passes(self, tmp_path, capsys):
        root = tree(tmp_path, "46 of 74 registry exchanges have automated fetchers as of v2.20.1.\n")
        (root / "VERSION").write_text("2.20.1\n")
        code, out, _ = run(root, capsys)
        assert code == 0 and "3 claim(s)" in out  # exchanges_total, fetchers_registered, version

    def test_stale_version_fails_naming_version_file(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\nAs of v2.15.4 the fetchers work.\n")
        (root / "VERSION").write_text("2.20.1\n")
        code, out, _ = run(root, capsys)
        assert code == 1
        assert "README.md:2" in out and "says 2.15.4" in out and "VERSION has 2.20.1" in out

    def test_version_file_whitespace_is_stripped(self, tmp_path, capsys):
        root = tree(tmp_path, "As of v2.20.1 the fetchers work.\n")
        (root / "VERSION").write_text("  2.20.1  \n\n")
        assert run(root, capsys)[0] == 0

    def test_prefix_of_a_longer_version_is_not_a_match(self, tmp_path, capsys):
        root = tree(tmp_path, "As of v2.20.1 the fetchers work.\n")
        (root / "VERSION").write_text("2.20.10\n")
        assert run(root, capsys)[0] == 1

    def test_version_claim_without_version_file_is_exit_two(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\nAs of v2.20.1 it works.\n")
        code, _, err = run(root, capsys)
        assert code == 2 and "VERSION" in err

    def test_as_of_without_a_version_is_ignored(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\nAs of today, and as of v2 later.\n")
        assert run(root, capsys)[0] == 0

    def test_version_claim_alone_satisfies_the_no_claim_rule(self, tmp_path, capsys):
        root = tree(tmp_path, "As of v2.20.1 it works.\n")
        (root / "VERSION").write_text("2.20.1\n")
        assert run(root, capsys)[0] == 0


class TestNotClaims:
    def test_bare_count_is_not_a_claim(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\n| Saturday-Sunday | 67 exchanges (includes UAE) |\n"
                              "| Friday-Saturday | 7 exchanges (Saudi) |\n")
        code, out, _ = run(root, capsys)
        assert code == 0 and "1 claim(s)" in out

    def test_fenced_code_is_skipped(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\n```\n99 exchanges across 6.\n```\n~~~\n99 exchanges.\n~~~\n")
        assert run(root, capsys)[0] == 0

    def test_command_output_sample_is_not_a_claim(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\n# Output: OK: 99 exchange file(s) validated\n")
        assert run(root, capsys)[0] == 0


class TestExitTwo:
    def test_no_claim_in_a_file(self, tmp_path, capsys):
        code, _, err = run(tree(tmp_path, "Nothing countable here.\n"), capsys)
        assert code == 2 and "no claim found" in err

    def test_second_file_without_claim(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\n")
        (root / "OTHER.md").write_text("Nothing here.\n")
        code, _, err = run(root, capsys, "README.md", "OTHER.md")
        assert code == 2 and "OTHER.md" in err

    def test_missing_file(self, tmp_path, capsys):
        code, _, err = run(tree(tmp_path, "74 exchanges across 6.\n"), capsys, "NOPE.md")
        assert code == 2 and "cannot read NOPE.md" in err

    def test_missing_facts(self, tmp_path, capsys):
        (tmp_path / "README.md").write_text("74 exchanges across 6.\n")
        code, _, err = run(tmp_path, capsys)
        assert code == 2 and "facts.json" in err

    def test_malformed_facts(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\n")
        (root / "docs" / "facts.json").write_text("{not json")
        assert run(root, capsys)[0] == 2

    def test_facts_not_an_object(self, tmp_path, capsys):
        root = tree(tmp_path, "74 exchanges across 6.\n")
        (root / "docs" / "facts.json").write_text("[1]")
        assert run(root, capsys)[0] == 2

    def test_fact_missing_from_facts_json(self, tmp_path, capsys):
        facts = {k: v for k, v in FACTS.items() if k != "exchanges_total"}
        code, _, err = run(tree(tmp_path, "74 exchanges across 6.\n", facts=facts), capsys)
        assert code == 2 and "exchanges_total" in err


class TestRealDocuments:
    def test_real_docs_pass(self, capsys):
        assert cdf.main([]) == 0

    @pytest.mark.parametrize("rel", cdf.DEFAULT_FILES)
    def test_every_default_file_has_a_claim(self, rel):
        facts = json.loads((ROOT / "docs" / "facts.json").read_text())
        version = (ROOT / "VERSION").read_text().strip()
        _, found = cdf.scan((ROOT / rel).read_text(encoding="utf-8"), facts, version)
        assert found >= 1, rel
