import re
from typing import List, Dict, Any, Union
from backend.utils.logger import Logger

# ── Token estimation: ~4 chars per token (conservative) ──────────────────────
CHARS_PER_TOKEN = 4
TARGET_MIN_TOKENS = 400
TARGET_MAX_TOKENS = 700
TARGET_MIN_CHARS  = TARGET_MIN_TOKENS * CHARS_PER_TOKEN   # 1600
TARGET_MAX_CHARS  = TARGET_MAX_TOKENS * CHARS_PER_TOKEN   # 2800
OVERLAP_RATIO     = 0.12   # 12% overlap (midpoint of 10–15%)


def _token_estimate(text: str) -> int:
    """Rough token count estimate"""
    return len(text) // CHARS_PER_TOKEN


def _merge_blocks_into_chunks(
    blocks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Hierarchical + Semantic chunker.
    Merges structured paragraph blocks (from document_loader) into
    semantically coherent chunks of 400–700 tokens with 10–15% sliding overlap.

    Each output chunk carries full metadata:
      text, section, parent_section, page, start_page, end_page, token_estimate
    """
    if not blocks:
        return []

    chunks: List[Dict[str, Any]] = []
    current_texts: List[str]   = []
    current_chars: int          = 0
    current_section: str        = blocks[0].get('section', 'General')
    current_parent:  str        = blocks[0].get('parent_section', 'General')
    start_page: int             = blocks[0].get('page', 1)

    def _flush(end_page: int):
        nonlocal current_texts, current_chars, current_section, current_parent, start_page
        if not current_texts:
            return
        text = ' '.join(current_texts).strip()
        if len(text) > 60:
            chunks.append({
                'text':           text,
                'section':        current_section,
                'parent_section': current_parent,
                'page':           start_page,
                'end_page':       end_page,
                'token_estimate': _token_estimate(text),
            })
        current_texts = []
        current_chars = 0

    def _apply_overlap():
        """Re-seed current buffer with trailing text for overlap continuity"""
        nonlocal current_texts, current_chars
        if not chunks:
            return
        overlap_target_chars = int(TARGET_MAX_CHARS * OVERLAP_RATIO)
        # Walk back from end of last chunk to capture ~overlap chars
        last_chunk_text = chunks[-1]['text']
        overlap_text = last_chunk_text[-overlap_target_chars:].strip()
        if overlap_text:
            current_texts  = [overlap_text]
            current_chars  = len(overlap_text)

    for block in blocks:
        block_text   = block.get('text', '').strip()
        block_sec    = block.get('section', 'General')
        block_parent = block.get('parent_section', 'General')
        block_page   = block.get('page', 1)
        block_chars  = len(block_text)

        if not block_text or block_chars < 20:
            continue

        # Section boundary → flush current chunk and start fresh
        section_changed = (block_sec != current_section) and current_texts
        if section_changed:
            _flush(block_page - 1)
            _apply_overlap()
            current_section = block_sec
            current_parent  = block_parent
            start_page      = block_page

        # If this single block already exceeds max size → split it further
        if block_chars > TARGET_MAX_CHARS:
            # Flush current buffer first
            if current_texts:
                _flush(block_page)
                _apply_overlap()

            # Split oversized block by sentences
            sentences = re.split(r'(?<=[.!?])\s+', block_text)
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if current_chars + len(sent) > TARGET_MAX_CHARS and current_chars >= TARGET_MIN_CHARS:
                    _flush(block_page)
                    _apply_overlap()
                    current_section = block_sec
                    current_parent  = block_parent
                    start_page      = block_page
                current_texts.append(sent)
                current_chars += len(sent) + 1
            continue

        # Normal accumulation
        would_exceed = (current_chars + block_chars) > TARGET_MAX_CHARS
        is_big_enough = current_chars >= TARGET_MIN_CHARS

        if would_exceed and is_big_enough:
            _flush(block_page)
            _apply_overlap()
            current_section = block_sec
            current_parent  = block_parent
            start_page      = block_page

        current_texts.append(block_text)
        current_chars += block_chars + 1

    # Final flush
    _flush(blocks[-1].get('page', 1) if blocks else 1)

    Logger.info(
        f"Hierarchical chunker produced {len(chunks)} chunks "
        f"(target {TARGET_MIN_TOKENS}–{TARGET_MAX_TOKENS} tokens, {int(OVERLAP_RATIO*100)}% overlap)."
    )
    return chunks


def split_text(text_or_blocks: Union[str, List[Dict[str, Any]]],
               chunk_size: int = 2400,
               overlap: int = 300) -> List[Dict[str, Any]]:
    """
    Public API — accepts either:
      a) structured block list from load_document_structured() → uses hierarchical chunker
      b) raw string                                            → falls back to basic splitter

    Always returns a list of dicts:
        { text, section, parent_section, page, end_page, token_estimate }
    """
    # ── Structured path ───────────────────────────────────────────────────────
    if isinstance(text_or_blocks, list):
        return _merge_blocks_into_chunks(text_or_blocks)

    # ── Legacy flat-string path ───────────────────────────────────────────────
    Logger.info("Splitting flat text using sliding-window recursive splitter (legacy path)...")
    text = text_or_blocks
    separators = ["\n\n", "\n", " ", ""]

    def recursive_split(t: str, seps: list) -> list:
        if len(t) <= chunk_size:
            return [t] if t.strip() else []
        sep = seps[-1]
        for s in seps:
            if s == "" or s in t:
                sep = s
                break
        parts = t.split(sep) if sep else list(t)
        parts = [p for p in parts if p]
        result, cur, cur_len = [], [], 0
        for part in parts:
            if len(part) > chunk_size and len(seps) > 1:
                if cur:
                    result.append(sep.join(cur))
                    cur, cur_len = [], 0
                result.extend(recursive_split(part, seps[1:]))
                continue
            add_len = len(part) + (len(sep) if cur else 0)
            if cur_len + add_len > chunk_size and cur:
                result.append(sep.join(cur))
                while cur_len > overlap and len(cur) > 1:
                    popped = cur.pop(0)
                    cur_len -= len(popped) + len(sep)
            cur.append(part)
            cur_len += add_len
        if cur:
            result.append(sep.join(cur))
        return result

    raw_chunks = recursive_split(text, separators)
    chunks = []
    for chunk_text in raw_chunks:
        clean = chunk_text.strip()
        if len(clean) > 30:
            chunks.append({
                'text':           clean,
                'section':        'Extracted Section',
                'parent_section': 'General',
                'page':           1,
                'end_page':       1,
                'token_estimate': _token_estimate(clean),
            })
    Logger.info(f"Legacy splitter produced {len(chunks)} chunks.")
    return chunks
