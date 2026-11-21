"""Extract page-addressable text from user-supplied public PDF reports."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import re


def extract_pdf(filename: str, content: bytes, record_key: str | None = None, source_url: str | None = None):
    """Extract PDF metadata and text passages; scanned PDFs are not OCRed."""
    try:
        import pymupdf as fitz
    except ImportError as exc:
        raise ValueError("PDF text extraction needs PyMuPDF. Install it with: python -m pip install pymupdf") from exc
    digest = sha256(content).hexdigest()
    try:
        pdf = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Could not read this PDF: {exc}") from exc
    metadata = dict(pdf.metadata or {})
    pages = []
    for page_no, page in enumerate(pdf, start=1):
        text = re.sub(r"\s+", " ", page.get_text("text")).strip()
        if not text:
            continue
        # Keep page references and manageable passages for deterministic retrieval.
        paragraphs = [part.strip() for part in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])|\n{2,}", page.get_text("text")) if part.strip()]
        if not paragraphs:
            paragraphs = [text]
        buffer = ""
        for paragraph in paragraphs:
            normalized = re.sub(r"\s+", " ", paragraph).strip()
            if len(buffer) + len(normalized) + 1 > 1200 and buffer:
                pages.append({"page_number": page_no, "passage": buffer})
                buffer = ""
            buffer = f"{buffer} {normalized}".strip()
        if buffer:
            pages.append({"page_number": page_no, "passage": buffer})
    if not pages:
        pdf.close()
        raise ValueError("No selectable text was found. Scanned/image-only PDFs are unsupported; OCR is not enabled.")
    document = {
        "document_id": sha256(f"{digest}:{record_key or ''}".encode("utf-8")).hexdigest(),
        "record_key": record_key,
        "filename": filename,
        "source_url": source_url,
        "sha256": digest,
        "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metadata": {
            "title": metadata.get("title") or "",
            "author": metadata.get("author") or "",
            "page_count": len(pdf),
            "pages_with_text": len({item["page_number"] for item in pages}),
            "extraction": "PyMuPDF text extraction; OCR not performed",
        },
    }
    pdf.close()
    for index, passage in enumerate(pages):
        passage["evidence_id"] = f"{document['document_id']}:{passage['page_number']}:{index}"
    return document, pages


def retrieve_passages(passages, query: str, limit: int = 12):
    """Rank passages with deterministic token overlap, returning cited source rows."""
    tokens = {token.casefold() for token in re.findall(r"[\w-]{3,}", query)}
    if not tokens:
        return []
    hits = []
    for passage in passages:
        text = str(passage.get("passage", ""))
        lowered = text.casefold()
        score = sum(lowered.count(token) for token in tokens)
        if score:
            hits.append({**passage, "match_score": score})
    return sorted(hits, key=lambda item: (-item["match_score"], int(item.get("page_number") or 0)))[:limit]
