"""Parse AV_FSCClassAssignment._151007.pdf -> data/fsc_catalog.json.

The DLA "FSC Class Assignments" PDF lists Federal Supply Class codes as

    NNNN   <description>   <RIC>/<ACTY>

where NNNN is the 4-digit FSC, the description may span multiple wrapped lines,
and RIC/ACTY (e.g. S9C/AX, FAA/75) sits at the end of the row.

This script extracts every (code, title) pair found in the document, dedupes,
and writes a stable JSON catalog the Classification Worker loads at startup.

Usage:
    python3 scripts/parse_fsc_pdf.py \
        --input AV_FSCClassAssignment._151007.pdf \
        --output data/fsc_catalog.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(
        "pdfplumber is required. Install with: pip install pdfplumber\n"
    )
    raise SystemExit(1) from exc


# RIC/ACTY pattern. Observed forms in the PDF include S9C/AX, S9I/KZ, FAA/75,
# 7FX/75, 6FE/75, 2FY/75, S9S/S9P, S9M/KX. So both sides are 2-4 alphanumerics
# but must contain at least one letter (we enforce that as a post-filter).
_RIC_ACTY = r"[A-Z0-9]{2,4}/[A-Z0-9]{2,4}"
_RIC_RE = re.compile(rf"^{_RIC_ACTY}$")

# Line-anchored row: <code> <title...> <RIC>
_ROW_LINE = re.compile(
    rf"^(?P<code>\d{{4}})\s+(?P<title>.+?)\s+(?P<ric>{_RIC_ACTY})\s*$"
)

# Lines that are pure page furniture and should be discarded before parsing.
_NOISE_LINES = re.compile(
    r"""^\s*(
        IV-\d+
      | FSC\s*(LISTING)?
      | CODE
      | DESCRIPTION
      | RIC\s*/?\s*ACTY
      | Table\s+\d.*
      | FEDERAL\s+SUPPLY.*
      | Each\s+item.*
      | Source\s+of.*
      | service/agency.*
      | The\s+following.*
      | Part\s+I.*
      | --\s*\d+\s+of\s+\d+\s*--
    )\s*$""",
    re.VERBOSE,
)


def extract_text(pdf_path: Path) -> str:
    chunks: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            chunks.append(text)
    return "\n".join(chunks)


def _ric_has_letter(ric: str) -> bool:
    return any(ch.isalpha() for ch in ric)


def normalize_title(raw: str) -> str:
    cleaned = re.sub(r"\s+", " ", raw).strip()
    # Drop trailing markers like ** or * that the PDF uses for footnotes.
    cleaned = re.sub(r"\s*\*+\s*$", "", cleaned).strip()
    return cleaned


def _clean_lines(raw_text: str) -> list[str]:
    out: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or _NOISE_LINES.match(stripped):
            continue
        out.append(stripped)
    return out


def _record(seen: dict[str, str], code: str, title: str) -> None:
    if not title or len(title) > 200:
        return
    if re.search(r"\b\d{4}\b", title):
        return
    if code in seen and len(seen[code]) >= len(title):
        return
    seen[code] = title


def parse(text: str) -> list[dict[str, str]]:
    lines = _clean_lines(text)
    seen: dict[str, str] = {}
    n = len(lines)

    row_full = re.compile(rf"^(\d{{4}})\s+(.+?)\s+({_RIC_ACTY})\s*$")
    row_code_ric_only = re.compile(rf"^(\d{{4}})\s+({_RIC_ACTY})\s*$")
    row_code_head = re.compile(r"^(\d{4})\s+(.+)$")
    line_ric_tail = re.compile(rf"^(.+?)\s+({_RIC_ACTY})\s*$")

    for i, line in enumerate(lines):
        m = row_full.match(line)
        if m and _ric_has_letter(m.group(3)):
            _record(seen, m.group(1), normalize_title(m.group(2)))
            continue

        m = row_code_ric_only.match(line)
        if m and _ric_has_letter(m.group(2)):
            # Title wrapped above/below this code+ric line.
            prev_line = lines[i - 1] if i > 0 else ""
            next_line = lines[i + 1] if i + 1 < n else ""
            if re.match(r"^\d{4}\s", prev_line):
                prev_line = ""
            if re.match(r"^\d{4}\s", next_line):
                next_line = ""
            _record(seen, m.group(1), normalize_title(f"{prev_line} {next_line}"))
            continue

        # Two-line wrap: code starts on this line; RIC sits at end of the next.
        m = row_code_head.match(line)
        if m and i + 1 < n:
            head = m.group(2)
            combined = f"{head} {lines[i + 1]}"
            m2 = line_ric_tail.match(combined)
            if m2 and _ric_has_letter(m2.group(2)):
                _record(seen, m.group(1), normalize_title(m2.group(1)))

    return [{"code": c, "title": seen[c]} for c in sorted(seen)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    if not args.input.exists():
        sys.stderr.write(f"Input PDF not found: {args.input}\n")
        return 1

    text = extract_text(args.input)
    entries = parse(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"Wrote {len(entries)} FSC entries to {args.output}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
