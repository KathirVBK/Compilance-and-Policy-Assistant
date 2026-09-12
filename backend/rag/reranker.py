import re
from typing import List, Dict, Any
from backend.llm import gemini
from backend.utils.logger import Logger

# ── Batch rerank system prompt ────────────────────────────────────────────────
# One LLM call scores ALL candidates at once — ~15x faster than per-chunk calls
BATCH_RERANK_SYSTEM_PROMPT = (
    "You are a Relevance Scoring Engine for a corporate policy compliance assistant. "
    "You will be given a user query and a numbered list of policy text chunks. "
    "Score each chunk's relevance to the query on a scale of 0-10.\n\n"
    "SCORING RULES:\n"
    "- 8-10: Directly answers the query with specific policy rules, numbers, or procedures.\n"
    "- 5-7: Related to the topic but only partially answers it.\n"
    "- 2-4: Mentions the general domain but is not specifically relevant.\n"
    "- 0-1: Unrelated to the query.\n\n"
    "OUTPUT FORMAT: Output ONLY a JSON array of integers, one score per chunk, in order.\n"
    "Example for 3 chunks: [8, 3, 6]\n"
    "No explanation. No extra text. Just the JSON array."
)


def rerank_chunks(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 6,
) -> List[Dict[str, Any]]:
    """
    Batch Cross-Encoder LLM Reranker.

    Sends ALL candidate chunks in a SINGLE LLM call (instead of N separate calls),
    parses the returned score array, then returns the top_k chunks sorted by score.

    Speed improvement: ~15x faster than per-chunk reranking.
    Falls back to FAISS cosine ordering if the LLM call or parsing fails.
    """
    if not candidates:
        return []

    if len(candidates) <= top_k:
        Logger.info(f"Reranker: {len(candidates)} candidates <= top_k={top_k} — skipping scoring.")
        return candidates

    # ── Build single batched prompt ───────────────────────────────────────────
    chunk_list_text = ""
    for i, chunk in enumerate(candidates, start=1):
        preview = chunk.get("rawText", chunk.get("content", ""))[:400]
        chunk_list_text += f"\n[{i}] {preview}\n"

    prompt = (
        f"User Query: {query}\n\n"
        f"Policy Chunks to score:\n{chunk_list_text}\n"
        f"Scores JSON array ({len(candidates)} integers):"
    )

    try:
        Logger.info(f"Reranker [BATCH]: scoring {len(candidates)} chunks in 1 LLM call...")
        raw = gemini.generate_response(
            prompt, BATCH_RERANK_SYSTEM_PROMPT, model_override="gemini-2.5-flash"
        )

        # Parse the JSON array from the response
        match = re.search(r'\[[\d,\s]+\]', (raw or ""))
        if match:
            scores = [int(x) for x in re.findall(r'\d+', match.group())]
        else:
            # Fallback: extract all integers in order
            scores = [int(x) for x in re.findall(r'\b(\d{1,2})\b', (raw or ""))]

        # Pad or truncate scores to match candidate count
        scores = scores[:len(candidates)]
        while len(scores) < len(candidates):
            scores.append(5)  # Default mid-score for missing entries

        # Clamp all scores to [0, 10]
        scores = [max(0, min(10, s)) for s in scores]

        Logger.info(f"Reranker [BATCH]: scores = {scores}")

        for chunk, score in zip(candidates, scores):
            chunk["rerank_score"] = score

    except Exception as exc:
        Logger.warn(f"Reranker [BATCH]: LLM call failed ({exc}). Using FAISS cosine ordering.")
        # Fall back: assign scores based on FAISS cosine similarity
        for chunk in candidates:
            chunk["rerank_score"] = int(chunk.get("score", 0.5) * 10)

    # Sort by rerank_score desc, break ties by FAISS cosine score
    candidates.sort(key=lambda c: (c["rerank_score"], c.get("score", 0)), reverse=True)
    top = candidates[:top_k]

    Logger.info(
        f"Reranker [BATCH]: selected top {len(top)} — "
        f"scores: {[c['rerank_score'] for c in top]}"
    )
    return top



