import os
import re
import fitz  # PyMuPDF
from backend.utils.logger import Logger

# ── Heading detection patterns ────────────────────────────────────────────────
_HEADING_PATTERNS = [
    re.compile(r'^(chapter|section|part|article)\s+[\dIVXivx]+', re.IGNORECASE),
    re.compile(r'^\d+(\.\d+)*\s+[A-Z]'),           # "1.2 PolicyTitle"
    re.compile(r'^[A-Z][A-Z\s]{4,40}$'),            # ALL CAPS short line
    re.compile(r'^[A-Z]\.\s+[A-Z]'),                # "A. Header"
]

def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 120:
        return False
    for pat in _HEADING_PATTERNS:
        if pat.match(line):
            return True
    return False

def clean_text(text: str) -> str:
    """Removes extra spaces and normalises newlines"""
    if not text:
        return ""
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def load_document(file_path: str):
    """
    Loads text from PDF or plain-text files.
    Returns a flat cleaned string (legacy API kept for non-PDF uploads).
    For structured extraction use load_document_structured().
    """
    if not os.path.exists(file_path):
        Logger.error(f"File not found: {file_path}")
        return None

    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        blocks = load_document_structured(file_path)
        if blocks is None:
            return None
        # Flatten to string for legacy callers
        return clean_text('\n\n'.join(b['text'] for b in blocks))
    else:
        Logger.info(f"Loading text file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return clean_text(f.read())
        except Exception as e:
            Logger.error(f"Failed to load text file {file_path}: {e}")
            return None

def load_document_structured(file_path: str):
    """
    Page-aware, section-tagged extraction from PDF.
    Returns list of dicts:
        { 'text': str, 'page': int, 'section': str, 'parent_section': str }
    Each dict represents a logical paragraph / block.
    """
    if not os.path.exists(file_path):
        Logger.error(f"File not found: {file_path}")
        return None

    Logger.info(f"Structured PDF extraction: {file_path}")
    try:
        doc = fitz.open(file_path)
        blocks = []
        current_section = "General"
        parent_section  = "General"

        for page_num, page in enumerate(doc, start=1):
            raw = page.get_text()
            if not raw:
                continue

            lines = raw.split('\n')
            paragraph_lines = []

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    # Empty line = paragraph break
                    if paragraph_lines:
                        para_text = ' '.join(paragraph_lines).strip()
                        if len(para_text) > 20:
                            blocks.append({
                                'text':           para_text,
                                'page':           page_num,
                                'section':        current_section,
                                'parent_section': parent_section,
                            })
                        paragraph_lines = []
                    continue

                if _is_heading(stripped):
                    # Flush any pending paragraph first
                    if paragraph_lines:
                        para_text = ' '.join(paragraph_lines).strip()
                        if len(para_text) > 20:
                            blocks.append({
                                'text':           para_text,
                                'page':           page_num,
                                'section':        current_section,
                                'parent_section': parent_section,
                            })
                        paragraph_lines = []

                    # Promote heading hierarchy
                    if re.match(r'^[A-Z][A-Z\s]{4,40}$', stripped):
                        parent_section  = stripped
                        current_section = stripped
                    else:
                        current_section = stripped
                else:
                    paragraph_lines.append(stripped)

            # Flush remaining lines at end of page
            if paragraph_lines:
                para_text = ' '.join(paragraph_lines).strip()
                if len(para_text) > 20:
                    blocks.append({
                        'text':           para_text,
                        'page':           page_num,
                        'section':        current_section,
                        'parent_section': parent_section,
                    })

        Logger.info(f"Structured extraction yielded {len(blocks)} paragraph blocks across {len(doc)} pages.")
        return blocks

    except Exception as e:
        Logger.error(f"Structured PDF extraction failed for {file_path}: {e}")
        return None
