"""
tests/test_check_doc_links.py -- Tests for tools/check_doc_links.py.

The checker verifies that README.md, BLOCKED.md and docs/FETCHERS.md link
to each other by anchor, and that the README exchange table agrees with
exchanges/*.json and BLOCKED.md.

What this file locks in:
    1.  A consistent mini repo passes (exit 0).
    2.  A link to a missing anchor, a missing file, or an anchor that only
        exists as a heading slug / explicit id is judged correctly.
    3.  Links inside code blocks and inline code are ignored; external
        URLs are not checked.
    4.  Duplicate explicit anchors are rejected.
    5.  README table: row count vs exchanges/, unknown or missing MIC,
        unsorted rows, Notes link pointing at another MIC, a status whose
        required link is absent.
    6.  Cross-document agreement: README blocked rows vs BLOCKED.md summary,
        BLOCKED.md index counts and class membership, FETCHERS.md anchors
        vs the README rows that link it.
    7.  Missing files exit 2.
    8.  The real repo passes, and its table has one row per exchange file.

All but the last test build their own mini repo with pytest's tmp_path.

Run:
    python3 -m pytest tests/test_check_doc_links.py -v
"""

import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_doc_links as checker  # noqa: E402

OK = "\u2705"
WARN = "\u26a0\ufe0f"
BLOCKED = "\u26d4"


def make_repo(tmp_path):
    """A small, consistent repo: XAAA implemented, XBBB blocked, XCCC
    CI-unreachable (both links)."""
    (tmp_path / "exchanges").mkdir()
    for mic in ("XAAA", "XBBB", "XCCC"):
        (tmp_path / "exchanges" / f"{mic}.json").write_text("{}")
    (tmp_path / "docs").mkdir()

    (tmp_path / "README.md").write_text(
        "# Registry\n\n"
        "| Exchange | MIC | Status | Source | Notes |\n"
        "|----------|-----|:------:|--------|-------|\n"
        f"| Alpha | XAAA | {OK} | alpha.example | [#xaaa](docs/FETCHERS.md#xaaa) |\n"
        f"| Beta | XBBB | {BLOCKED} | beta.example | [BLOCKED.md#xbbb](BLOCKED.md#xbbb) |\n"
        f"| Gamma | XCCC | {WARN} | gamma.example | [#xccc](docs/FETCHERS.md#xccc), "
        "[BLOCKED.md#xccc](BLOCKED.md#xccc) |\n"
    )
    (tmp_path / "BLOCKED.md").write_text(
        "# Blocked\n\n"
        "# Index\n\n"
        "| Class | Count | Exchanges |\n"
        "|---|---:|---|\n"
        "| [JS SPA](#js-spa) | 1 | [XBBB](#xbbb) |\n"
        "| [Closed API](#closed-api) | 0 | none |\n\n"
        '<a id="js-spa"></a>\n# JS SPA\n\n'
        '<a id="xbbb"></a>\n## XBBB — Beta\n\n**Last verified:** 2026-10-01\n\n'
        '<a id="closed-api"></a>\n# Closed API\n\n'
        '<a id="xccc"></a>\n## XCCC — Gamma\n\n**Last verified:** 2026-10-01\n\n'
        "# Summary\n\n"
        "| Code | Exchange | State |\n"
        "|------|----------|-------|\n"
        "| XAAA | Alpha | built |\n"
        "| XBBB | Beta | blocked |\n"
        "| XCCC | Gamma | CI-unreachable |\n"
    )
    (tmp_path / "docs" / "FETCHERS.md").write_text(
        "# Fetchers\n\n"
        '<a id="xaaa"></a>\n## Alpha (XAAA)\n\nnote\n\n'
        '<a id="xccc"></a>\n## Gamma (XCCC)\n\nnote\n'
    )
    return tmp_path


def edit(root, rel, old, new):
    p = root / rel
    text = p.read_text()
    assert old in text, f"{old!r} not in {rel}"
    p.write_text(text.replace(old, new, 1))


def run(root):
    code, report = checker.run_check(root)
    return code, "\n".join(report)


# ---------------------------------------------------------------- baseline

def test_consistent_repo_passes(tmp_path):
    code, report = run(make_repo(tmp_path))
    assert code == 0, report
    assert "3 rows for 3 exchange files" in report
    assert "OK:" in report


# ------------------------------------------------------------------- links

def test_missing_anchor_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "docs/FETCHERS.md", '<a id="xaaa"></a>', '<a id="xaaa-renamed"></a>')
    code, report = run(root)
    assert code == 1
    assert "no anchor #xaaa in docs/FETCHERS.md" in report


def test_missing_file_target_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", "# Registry\n", "# Registry\n\nSee [guide](docs/NOPE.md).\n")
    code, report = run(root)
    assert code == 1
    assert "link target not found: docs/NOPE.md" in report


def test_heading_slug_fragment_resolves(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", "# Registry\n", "# Registry\n\n[idx](BLOCKED.md#index) [sum](BLOCKED.md#summary)\n")
    code, report = run(root)
    assert code == 0, report


def test_heading_slug_keeps_double_hyphen_like_github(tmp_path):
    root = make_repo(tmp_path)
    # "## XBBB — Beta" slugs to xbbb--beta on GitHub (the dash is dropped,
    # both surrounding spaces become hyphens).
    edit(root, "README.md", "# Registry\n", "# Registry\n\n[b](BLOCKED.md#xbbb--beta)\n")
    code, report = run(root)
    assert code == 0, report


def test_same_file_fragment_is_checked(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "BLOCKED.md", "# Index\n", "# Index\n\n[x](#nowhere)\n")
    code, report = run(root)
    assert code == 1
    assert "no anchor #nowhere in BLOCKED.md" in report


def test_links_in_code_are_ignored(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", "# Registry\n",
         "# Registry\n\nUse `[x](docs/NOPE.md#a)` like this.\n\n```\n[y](docs/NOPE2.md#b)\n```\n")
    code, report = run(root)
    assert code == 0, report


def test_external_links_are_not_checked(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", "# Registry\n",
         "# Registry\n\n[web](https://example.invalid/a#b) [mail](mailto:a@b.invalid)\n")
    code, report = run(root)
    assert code == 0, report


def test_duplicate_explicit_anchor_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "docs/FETCHERS.md", '<a id="xaaa"></a>', '<a id="xaaa"></a>\n<a id="xaaa"></a>')
    code, report = run(root)
    assert code == 1
    assert 'duplicate anchor id "xaaa"' in report


# ----------------------------------------------------------- README table

def test_row_count_mismatch_fails(tmp_path):
    root = make_repo(tmp_path)
    (root / "exchanges" / "XDDD.json").write_text("{}")
    code, report = run(root)
    assert code == 1
    assert "table has 3 rows, exchanges/ has 4 files" in report
    assert "no table row for: XDDD" in report


def test_row_without_exchange_file_fails(tmp_path):
    root = make_repo(tmp_path)
    (root / "exchanges" / "XCCC.json").unlink()
    code, report = run(root)
    assert code == 1
    assert "table row has no exchanges/ file: XCCC" in report


def test_unsorted_rows_fail(tmp_path):
    root = make_repo(tmp_path)
    text = (root / "README.md").read_text().split("\n")
    i = next(n for n, l in enumerate(text) if "| XAAA |" in l)
    text[i], text[i + 1] = text[i + 1], text[i]
    (root / "README.md").write_text("\n".join(text))
    code, report = run(root)
    assert code == 1
    assert "not sorted by MIC" in report


def test_notes_link_for_another_mic_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", "[#xaaa](docs/FETCHERS.md#xaaa)", "[#xccc](docs/FETCHERS.md#xccc)")
    code, report = run(root)
    assert code == 1
    assert "points at #xccc, not #xaaa" in report


def test_implemented_row_without_fetchers_link_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", "[#xaaa](docs/FETCHERS.md#xaaa)", "none")
    code, report = run(root)
    assert code == 1
    assert "implemented row has no FETCHERS.md link" in report


def test_blocked_row_without_blocked_link_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", "[BLOCKED.md#xbbb](BLOCKED.md#xbbb)", "none")
    code, report = run(root)
    assert code == 1
    assert "blocked row has no BLOCKED.md link" in report


def test_warning_row_needs_both_links(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "README.md", ", [BLOCKED.md#xccc](BLOCKED.md#xccc)", "")
    code, report = run(root)
    assert code == 1
    assert "CI-unreachable row needs FETCHERS.md and BLOCKED.md links" in report


# ---------------------------------------------------- cross-document sync

def test_readme_blocked_vs_summary_mismatch_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "BLOCKED.md", "| XBBB | Beta | blocked |", "| XBBB | Beta | built |")
    code, report = run(root)
    assert code == 1
    assert "README blocked rows differ from BLOCKED.md summary" in report


def test_summary_missing_an_exchange_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "BLOCKED.md", "| XAAA | Alpha | built |\n", "")
    code, report = run(root)
    assert code == 1
    assert "summary table does not list exactly the exchanges/ files" in report


def test_index_count_mismatch_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "BLOCKED.md", "| [JS SPA](#js-spa) | 1 |", "| [JS SPA](#js-spa) | 2 |")
    code, report = run(root)
    assert code == 1
    assert 'index says 2 for "JS SPA" but lists 1' in report


def test_blocked_exchange_missing_from_index_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "BLOCKED.md", "| [JS SPA](#js-spa) | 1 | [XBBB](#xbbb) |",
         "| [JS SPA](#js-spa) | 0 | none |")
    code, report = run(root)
    assert code == 1
    assert "index classes differ" in report


def test_exchange_in_two_classes_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "BLOCKED.md", "| [Closed API](#closed-api) | 0 | none |",
         "| [Closed API](#closed-api) | 1 | [XBBB](#xbbb) |")
    code, report = run(root)
    assert code == 1
    assert "filed under more than one class: XBBB" in report


def test_fetchers_anchor_without_readme_link_fails(tmp_path):
    root = make_repo(tmp_path)
    edit(root, "docs/FETCHERS.md", '<a id="xaaa"></a>', '<a id="xaaa"></a>\n<a id="xzzz"></a>')
    code, report = run(root)
    assert code == 1
    assert "FETCHERS only: xzzz" in report


# --------------------------------------------------------------- plumbing

@pytest.mark.parametrize("missing", ["README.md", "BLOCKED.md", "docs/FETCHERS.md"])
def test_missing_document_exits_2(tmp_path, missing):
    root = make_repo(tmp_path)
    (root / missing).unlink()
    code, report = run(root)
    assert code == 2
    assert "required document not found" in report


def test_missing_exchanges_dir_exits_2(tmp_path):
    root = make_repo(tmp_path)
    for p in (root / "exchanges").glob("*.json"):
        p.unlink()
    (root / "exchanges").rmdir()
    code, _ = run(root)
    assert code == 2


def test_main_returns_exit_code(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert checker.main(["check_doc_links.py", "--root", str(root)]) == 0
    assert "OK:" in capsys.readouterr().out
    edit(root, "docs/FETCHERS.md", '<a id="xaaa"></a>', '<a id="xaaa-renamed"></a>')
    assert checker.main(["check_doc_links.py", "--root", str(root)]) == 1
    assert checker.main(["check_doc_links.py", "--bogus"]) == 2


# ------------------------------------------------------------------- real

def test_real_repo_passes_and_table_has_a_row_per_exchange():
    repo_root = Path(__file__).parent.parent
    if not (repo_root / "exchanges").exists() or not (repo_root / "README.md").exists():
        pytest.skip("real repo files not present in this checkout")
    code, report = checker.run_check(repo_root)
    assert code == 0, "\n".join(report)
    n_files = len(list((repo_root / "exchanges").glob("*.json")))
    assert f"{n_files} rows for {n_files} exchange files" in "\n".join(report)
