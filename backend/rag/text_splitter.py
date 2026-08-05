import re
from backend.utils.logger import Logger

# ─────────────────────────────────────────────────────────────────
# Table detection helpers
# ─────────────────────────────────────────────────────────────────

def _is_table_line(line: str) -> bool:
    """Returns True if the line looks like part of a plain-text table,
    pipe-delimited markdown table, tabbed list, or bulleted key-value table."""
    stripped = line.strip()
    if not stripped:
        return False
    # Pipe-delimited markdown/ASCII table
    if stripped.count('|') >= 2:
        return True
    # Rows that contain at least 2 tab-separated or multi-space-separated columns
    cols = re.split(r'\s{2,}|\t', stripped)
    if len(cols) >= 3 and any(c.strip() for c in cols):
        return True
    # Bulleted table/rate list (e.g., "- Full-Time < 5 years service: 5.0 accrual rate...")
    if re.match(r'^\s*[-*•]?\s*[A-Z\w\s\<\>\=\@\-\(\)]+:\s*\d', stripped):
        return True
    return False


def _extract_tables_and_prose(text: str):
    """
    Walks through raw text line by line and returns structured segments:
      {'type': 'table'|'prose', 'content': <str>, 'section': <str>, 'page': <int>}
    Consecutive table lines are grouped as single atomic blocks.
    """
    lines = text.splitlines()
    segments = []
    current_type = None
    current_lines = []
    current_section = ""
    current_page = 1
    has_explicit_pages = "\n--- Page " in text or text.startswith("--- Page ")

    page_marker_re = re.compile(r'^\s*---\s*Page\s+(\d+)\s*---\s*$', re.IGNORECASE)
    section_re = re.compile(r'^(#{1,4}|[A-Z0-9\s\(\)\/\&\-\.\,]{3,60}:?)\s*$')

    def flush(seg_type, seg_lines, section, page):
        content = '\n'.join(seg_lines).strip()
        if content:
            segments.append({'type': seg_type, 'content': content, 'section': section, 'page': page})

    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        
        # Track explicit page markers or estimate from line index
        page_match = page_marker_re.match(stripped)
        if page_match:
            current_page = int(page_match.group(1))
            continue
        elif not has_explicit_pages:
            current_page = (line_idx // 35) + 1
        
        # Track section headings (all caps or markdown headings < 80 chars not matching a full table line)
        if stripped and len(stripped) < 80 and not _is_table_line(line):
            if (stripped.isupper() and len(stripped) >= 3) or stripped.startswith('#') or stripped.endswith(':'):
                flush(current_type or 'prose', current_lines, current_section, current_page)
                current_lines = []
                current_type = None
                current_section = stripped.lstrip('#').strip().rstrip(':').strip()
                continue

        is_table = _is_table_line(line)

        if is_table:
            if current_type != 'table':
                flush(current_type or 'prose', current_lines, current_section, current_page)
                current_lines = []
                current_type = 'table'
        else:
            if current_type == 'table':
                flush('table', current_lines, current_section, current_page)
                current_lines = []
                current_type = 'prose'

        current_lines.append(line)

    flush(current_type or 'prose', current_lines, current_section, current_page)
    return segments


# ─────────────────────────────────────────────────────────────────
# Core chunker
# ─────────────────────────────────────────────────────────────────

def split_text(text, chunk_size=800, overlap=160):
    """
    Splits document text into chunks with:
    - Atomic table blocks preserving complete table/row identities
    - 15-20% character overlap for prose sections
    - Section title and page number metadata for grounded traceability
    """
    segments = _extract_tables_and_prose(text)
    chunks = []         # list of {'text': str, 'section': str, 'page': int}

    for seg in segments:
        content = seg['content']
        section = seg['section']
        page = seg['page']

        # ── Tables: keep as a single atomic chunk when possible ──
        if seg['type'] == 'table':
            if len(content) <= chunk_size * 2:
                chunks.append({'text': content, 'section': section, 'page': page})
            else:
                rows = content.splitlines()
                header = rows[0] if rows else ''
                batch = [f"[Table Header / Context: {header}]"] if header else []
                batch_len = len(header)
                for row in rows[1:]:
                    if batch_len + len(row) + 1 > chunk_size * 2:
                        chunks.append({'text': '\n'.join(batch), 'section': section, 'page': page})
                        batch = [f"[Table Header / Context: {header}]", row]
                        batch_len = len(header) + len(row) + 1
                    else:
                        batch.append(row)
                        batch_len += len(row) + 1
                if batch:
                    chunks.append({'text': '\n'.join(batch), 'section': section, 'page': page})
            continue

        # ── Prose: sliding window with 15-20% overlap ─────────────
        clean = " ".join(content.split())
        start = 0
        while start < len(clean):
            end = min(start + chunk_size, len(clean))

            # Align to sentence boundary
            if end < len(clean):
                search_zone = clean[max(start, end - overlap): end + 20]
                best = -1
                for punct in ['. ', '! ', '? ', '.\n', '\n']:
                    idx = search_zone.find(punct)
                    if idx != -1:
                        candidate = max(start, end - overlap) + idx + len(punct)
                        if candidate > start:
                            best = candidate
                            break
                if best > start:
                    end = best
                else:
                    space_idx = clean.rfind(' ', start, end)
                    if space_idx > start:
                        end = space_idx

            chunk_text = clean[start:end].strip()
            if len(chunk_text) > 30:          # discard tiny orphan fragments
                chunks.append({'text': chunk_text, 'section': section, 'page': page})

            next_start = end - overlap
            if next_start <= start:
                next_start = end
            start = next_start
            if start >= len(clean):
                break

    Logger.info(f"Split document into {len(chunks)} chunks ({sum(1 for c in chunks if c['section'])} with section metadata).")
    return chunks

