#!/usr/bin/env python3
"""
check_doc_links.py -- Cross-document link and exchange-table consistency.

README.md, BLOCKED.md and docs/FETCHERS.md point at each other by anchor
(`docs/FETCHERS.md#xnys`, `BLOCKED.md#xses`). A renamed or reordered section
breaks those links silently: GitHub just opens the top of the page. This
check makes it loud.

What it checks
--------------
1. Links. Every relative markdown link in the three documents resolves: the
   target file exists, and if the link carries a #fragment and the target is
   a markdown file, the fragment names an explicit `<a id="...">` anchor or a
   heading slug in that file. External URLs are not checked. Code blocks and
   inline code are ignored. Explicit anchors must be unique within a file.
2. The README exchange table (rows of `| name | MIC | status | source |
   notes |`): one row per exchanges/*.json, sorted by MIC; status is one of
   the three icons; the Notes links of each row point at that row's own MIC
   (`#xnys` for XNYS); a green row links FETCHERS.md, a warning row links
   both FETCHERS.md and BLOCKED.md, a blocked row links BLOCKED.md.
3. Agreement between documents:
   - the README's blocked rows are exactly the `blocked` rows of the
     BLOCKED.md summary table, and that table lists every exchange;
   - the BLOCKED.md index table files each blocked exchange under exactly
     one class, and each class's count equals the exchanges it lists;
   - the MIC anchors in FETCHERS.md are exactly the README rows that link
     FETCHERS.md.

Usage:
    check_doc_links.py [--root PATH]

    --root defaults to the repository root (the parent of tools/).

Exit codes:
    0 -- every check passed
    1 -- at least one failure (each is printed with file and line)
    2 -- a required file or directory is missing
"""

import re
import sys
from pathlib import Path

DOCS = ("README.md", "BLOCKED.md", "docs/FETCHERS.md")

ICON_OK = "\u2705"
ICON_WARN = "\u26a0\ufe0f"
ICON_BLOCKED = "\u26d4"

LINK_RE = re.compile(r'(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
ANCHOR_RE = re.compile(r'<a\s+(?:id|name)="([^"]+)"\s*>', re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
ROW_RE = re.compile(
    r"^\| (?P<name>.+?) \| (?P<mic>DSMD|X[A-Z]{3}) \| "
    r"(?P<status>\u2705|\u26a0\ufe0f?|\u26d4) \| (?P<source>.+?) \| (?P<notes>.+) \|$"
)
SUMMARY_ROW_RE = re.compile(
    r"^\| (DSMD|X[A-Z]{3}) \| .+? \| (built|blocked|CI-unreachable|resolved) \|$"
)
INDEX_ROW_RE = re.compile(r"^\| \[([^\]]+)\]\(#([a-z0-9-]+)\) \| (\d+) \| (.+) \|$")
MIC_LINK_RE = re.compile(r"\[((?:DSMD|X[A-Z]{3}))\]\(#([a-z0-9]+)\)")


def mask_code(text):
    """Blank out fenced code blocks and inline code, keeping line numbers."""
    out = []
    in_fence = False
    for line in text.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        out.append(re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), line))
    return "\n".join(out)


def github_slug(heading):
    """Approximation of GitHub's heading anchor: lowercase, drop everything
    but word characters, spaces and hyphens, then spaces become hyphens."""
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    h = re.sub(r"<[^>]+>", "", h)
    h = re.sub(r"[`*~]", "", h).strip().lower()
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


class Doc:
    def __init__(self, root, rel):
        self.rel = rel
        self.path = root / rel
        self.text = self.path.read_text(encoding="utf-8")
        self.masked = mask_code(self.text)
        self.explicit = ANCHOR_RE.findall(self.masked)
        self.slugs = []
        seen = {}
        for line in self.masked.split("\n"):
            m = HEADING_RE.match(line)
            if not m:
                continue
            s = github_slug(m.group(2))
            n = seen.get(s, 0)
            seen[s] = n + 1
            self.slugs.append(s if n == 0 else f"{s}-{n}")

    def anchors(self):
        return set(self.explicit) | set(self.slugs)


def run_check(root):
    """Returns (exit_code, report_lines)."""
    root = Path(root)
    exchanges_dir = root / "exchanges"
    if not exchanges_dir.is_dir():
        return 2, [f"ERROR: exchanges directory not found: {exchanges_dir}"]
    for rel in DOCS:
        if not (root / rel).is_file():
            return 2, [f"ERROR: required document not found: {root / rel}"]

    docs = {rel: Doc(root, rel) for rel in DOCS}
    errors = []
    stats = {"links": 0, "fragments": 0}

    # ---- 1. links and anchors
    for rel, doc in docs.items():
        dups = sorted({a for a in doc.explicit if doc.explicit.count(a) > 1})
        for a in dups:
            errors.append(f'{rel}: duplicate anchor id "{a}"')
        for lineno, line in enumerate(doc.masked.split("\n"), start=1):
            for bang, _text, target in LINK_RE.findall(line):
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue  # external (http, https, mailto, ...)
                stats["links"] += 1
                path_part, _, frag = target.partition("#")
                if path_part:
                    resolved = (doc.path.parent / path_part).resolve()
                    tname = path_part
                else:
                    resolved = doc.path
                    tname = rel
                if not resolved.exists():
                    errors.append(f"{rel}:{lineno}: link target not found: {target}")
                    continue
                if frag and not bang and resolved.suffix == ".md":
                    stats["fragments"] += 1
                    try:
                        key = str(resolved.relative_to(root.resolve()))
                    except ValueError:
                        key = None
                    tdoc = docs.get(key) if key else None
                    if tdoc is None:
                        tdoc = Doc(root, str(resolved.relative_to(root.resolve())))
                        docs[key] = tdoc
                    if frag not in tdoc.anchors():
                        errors.append(
                            f"{rel}:{lineno}: no anchor #{frag} in {key or tname} "
                            f"(link: {target})"
                        )

    # ---- 2. README exchange table
    mics_on_disk = sorted(p.stem for p in exchanges_dir.glob("*.json"))
    rows = []
    readme_lines = docs["README.md"].masked.split("\n")
    for lineno, line in enumerate(readme_lines, start=1):
        m = ROW_RE.match(line)
        if m:
            d = m.groupdict()
            d["line"] = lineno
            d["status"] = ICON_WARN if d["status"].startswith("\u26a0") else d["status"]
            rows.append(d)
    row_mics = [r["mic"] for r in rows]
    if len(rows) != len(mics_on_disk):
        errors.append(
            f"README.md: exchange table has {len(rows)} rows, "
            f"exchanges/ has {len(mics_on_disk)} files"
        )
    dup_rows = sorted({m for m in row_mics if row_mics.count(m) > 1})
    if dup_rows:
        errors.append(f"README.md: MIC listed more than once: {', '.join(dup_rows)}")
    missing = sorted(set(mics_on_disk) - set(row_mics))
    extra = sorted(set(row_mics) - set(mics_on_disk))
    if missing:
        errors.append(f"README.md: no table row for: {', '.join(missing)}")
    if extra:
        errors.append(f"README.md: table row has no exchanges/ file: {', '.join(extra)}")
    if row_mics != sorted(row_mics):
        errors.append("README.md: exchange table is not sorted by MIC")

    fetchers_rows = set()
    for r in rows:
        mic_l = r["mic"].lower()
        f_links = re.findall(r"\]\(docs/FETCHERS\.md#([a-z0-9-]+)\)", r["notes"])
        b_links = re.findall(r"\]\(BLOCKED\.md#([a-z0-9-]+)\)", r["notes"])
        where = f"README.md:{r['line']}: {r['mic']}"
        for frag in f_links + b_links:
            if frag != mic_l:
                errors.append(f"{where}: Notes link points at #{frag}, not #{mic_l}")
        st = r["status"]
        if st == ICON_OK and not f_links:
            errors.append(f"{where}: implemented row has no FETCHERS.md link")
        if st == ICON_WARN and not (f_links and b_links):
            errors.append(f"{where}: CI-unreachable row needs FETCHERS.md and BLOCKED.md links")
        if st == ICON_BLOCKED and not b_links:
            errors.append(f"{where}: blocked row has no BLOCKED.md link")
        if f_links:
            fetchers_rows.add(mic_l)

    # ---- 3. agreement between documents
    readme_blocked = {r["mic"] for r in rows if r["status"] == ICON_BLOCKED}

    summary = {}
    for line in docs["BLOCKED.md"].masked.split("\n"):
        m = SUMMARY_ROW_RE.match(line)
        if m:
            summary[m.group(1)] = m.group(2)
    if sorted(summary) != mics_on_disk:
        miss = sorted(set(mics_on_disk) - set(summary))
        ext = sorted(set(summary) - set(mics_on_disk))
        errors.append(
            "BLOCKED.md: summary table does not list exactly the exchanges/ files"
            + (f" (missing: {', '.join(miss)})" if miss else "")
            + (f" (unknown: {', '.join(ext)})" if ext else "")
        )
    summary_blocked = {m for m, s in summary.items() if s == "blocked"}
    if readme_blocked != summary_blocked:
        errors.append(
            "README blocked rows differ from BLOCKED.md summary `blocked` rows "
            f"(README only: {', '.join(sorted(readme_blocked - summary_blocked)) or '-'}; "
            f"BLOCKED.md only: {', '.join(sorted(summary_blocked - readme_blocked)) or '-'})"
        )

    class_mics = []
    index_rows = 0
    for lineno, line in enumerate(docs["BLOCKED.md"].masked.split("\n"), start=1):
        m = INDEX_ROW_RE.match(line)
        if not m:
            continue
        index_rows += 1
        name, _cid, count, cell = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        listed = [mic for mic, _ in MIC_LINK_RE.findall(cell)]
        if count != len(listed):
            errors.append(
                f"BLOCKED.md:{lineno}: index says {count} for \"{name}\" but lists {len(listed)}"
            )
        class_mics += listed
    dup_class = sorted({m for m in class_mics if class_mics.count(m) > 1})
    if dup_class:
        errors.append(f"BLOCKED.md: filed under more than one class: {', '.join(dup_class)}")
    if index_rows == 0:
        errors.append("BLOCKED.md: no class index table found")
    elif set(class_mics) != summary_blocked:
        errors.append(
            "BLOCKED.md index classes differ from the summary `blocked` rows "
            f"(index only: {', '.join(sorted(set(class_mics) - summary_blocked)) or '-'}; "
            f"summary only: {', '.join(sorted(summary_blocked - set(class_mics))) or '-'})"
        )

    fetchers_anchors = {
        a for a in docs["docs/FETCHERS.md"].explicit if re.fullmatch(r"[a-z]{4}", a)
    }
    if fetchers_anchors != fetchers_rows:
        errors.append(
            "docs/FETCHERS.md MIC anchors differ from README rows that link it "
            f"(FETCHERS only: {', '.join(sorted(fetchers_anchors - fetchers_rows)) or '-'}; "
            f"README only: {', '.join(sorted(fetchers_rows - fetchers_anchors)) or '-'})"
        )

    counts = {i: sum(1 for r in rows if r["status"] == i) for i in (ICON_OK, ICON_WARN, ICON_BLOCKED)}
    report = [
        f"Documents: {', '.join(DOCS)}",
        f"Links checked: {stats['links']} ({stats['fragments']} with a fragment)",
        f"README exchange table: {len(rows)} rows for {len(mics_on_disk)} exchange files "
        f"({counts[ICON_OK]} {ICON_OK}, {counts[ICON_WARN]} {ICON_WARN}, {counts[ICON_BLOCKED]} {ICON_BLOCKED})",
        f"BLOCKED.md: {len(summary_blocked)} blocked, {len(class_mics)} filed under {index_rows} classes",
        f"FETCHERS.md: {len(fetchers_anchors)} MIC anchors",
    ]
    if errors:
        report.append("")
        report.append(f"FAIL ({len(errors)}):")
        report += [f"  - {e}" for e in errors]
        return 1, report
    report.append("")
    report.append("OK: all links resolve and the documents agree.")
    return 0, report


def main(argv):
    root = Path(__file__).resolve().parent.parent
    args = list(argv[1:])
    i = 0
    while i < len(args):
        if args[i] == "--root" and i + 1 < len(args):
            root = Path(args[i + 1])
            i += 2
        else:
            print(f"ERROR: unknown argument {args[i]!r}")
            print("Usage: check_doc_links.py [--root PATH]")
            return 2
    code, report = run_check(root)
    for line in report:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
