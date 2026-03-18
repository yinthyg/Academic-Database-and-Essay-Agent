import mimetypes
from pathlib import Path
from typing import List

import pandas as pd
import pdfplumber
from docx import Document as DocxDocument
from pypdf import PdfReader


def detect_mime_type(file_path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(file_path))
    return mime or "application/octet-stream"


def extract_text_from_pdf(path: Path) -> str:
    # Try pdfplumber first for better table handling
    try:
        texts: List[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                texts.append(page.extract_text() or "")
        joined = "\n".join(texts).strip()
        if joined:
            return joined
    except Exception:
        pass

    # Fallback to pypdf
    reader = PdfReader(str(path))
    pages_text: List[str] = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text).strip()


def extract_text_from_docx(path: Path) -> str:
    doc = DocxDocument(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs).strip()


def extract_text_from_xlsx(path: Path) -> str:
    # Each row as a separate line with comma-joined cells
    dfs = pd.read_excel(str(path), sheet_name=None, dtype=str)
    lines: List[str] = []
    for sheet_name, df in dfs.items():
        df = df.fillna("")
        for _, row in df.iterrows():
            row_text = ", ".join([str(v) for v in row.tolist() if str(v).strip()])
            if row_text:
                lines.append(f"[{sheet_name}] {row_text}")
    return "\n".join(lines).strip()


def extract_text_from_file(path: Path) -> str:
    mime = detect_mime_type(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    if suffix == ".xlsx":
        return extract_text_from_xlsx(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    # Best effort fallback: try reading as text
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

