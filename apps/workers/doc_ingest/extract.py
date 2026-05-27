"""PDF text extraction and normalization."""

from __future__ import annotations

import os
import re

import pdfplumber

MAX_CHARS = 50_000


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text[:MAX_CHARS]


def extract_text(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise ValueError(f"File is not a PDF: {file_path}")

    pages: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)

    raw = "\n\n".join(pages)
    return normalize_text(raw)
