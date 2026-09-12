import os
import re
from typing import List, Dict
from backend.llm import gemini
from backend.utils.logger import Logger

SYSTEM_MULTI_QUERY_PROMPT = (
    "You are a Query Expansion Engine for a corporate policy compliance assistant. "
    "Given a user query, generate 3 semantically diverse reformulations that together cover different facets: "
    "the direct rule, exceptions/edge cases, and penalties or procedures.\n\n"
    "RULES:\n"
    "1. Output EXACTLY 3 queries, one per line, numbered 1. 2. 3.\n"
    "2. Each query must be standalone and retrievable against a policy vector database.\n"
    "3. Do NOT include the original query in the output.\n"
    "4. Keep each query concise (under 25 words)."
)

SYSTEM_REWRITE_PROMPT = (
    "You are a Query Contextualizer. Given the conversation history and the latest user question, "
    "rewrite the latest question into a standalone, self-contained search query that incorporates all "
    "necessary context (such as specific policy topic names, subject matter, or referenced entities).\n\n"
    "RULES:\n"
    "1. If the question is already standalone and clear, return it UNCHANGED.\n"
    "2. If the user question contains ambiguous references (e.g., 'on it', 'tell me more about that', 'how about it', 'give details on that') "
    "AND the conversation history is empty or does NOT contain enough context to identify the specific policy topic, "
    "output EXACTLY the text: AMBIGUOUS_CLARIFICATION_REQUIRED.\n"
    "3. Do NOT answer the question. Only output the rewritten standalone search query or AMBIGUOUS_CLARIFICATION_REQUIRED.\n"
    "4. Keep the rewritten query natural, concise, and focused for vector database retrieval."
)

AMBIGUOUS_PATTERNS = [
    r'^(?:can you|please\s+)?(?:give|provide)\s+(?:me\s+)?(?:a\s+)?(?:more\s+|detailed\s+)?(?:description|details|info|information)\s+on\s+it\s*$',
    r'^(?:tell|explain)\s+me\s+more\s+(?:about\s+it|on\s+it|about\s+that)\s*$',
    r'^(?:how\s+about\s+it|what\s+about\s+it|what\s+about\s+that)\s*$',
    r'^(?:details\s+on\s+it|more\s+info\s+on\s+it)\s*$'
]

def rewrite_query(query: str, history: List[Dict[str, str]] = None) -> str:
    """
    Rewrites an ambiguous or follow-up query into a standalone query using recent chat history.
    If the reference cannot be resolved (no history or abrupt topic shift), returns 'AMBIGUOUS_CLARIFICATION_REQUIRED'.
    """
    clean_q = query.strip()
    has_history = history is not None and len(history) > 0

    # Rule 1: If history is empty and query is a pure ambiguous pronoun reference
    if not has_history:
        for pat in AMBIGUOUS_PATTERNS:
            if re.search(pat, clean_q, re.IGNORECASE):
                Logger.info(f"Query Rewriter -> Ambiguous reference without history detected: '{clean_q}'")
                return "AMBIGUOUS_CLARIFICATION_REQUIRED"

    # Format history turns
    history_text = ""
    if has_history:
        recent_history = history[-10:]  # Extended from 4 to 10 for richer multi-turn context
        for msg in recent_history:
            sender = "User" if msg.get("sender") == "user" else "Assistant"
            text = msg.get("text", "")
            if sender == "Assistant" and len(text) > 500:
                text = text[:500] + "..."
            history_text += f"{sender}: {text}\n"

    user_prompt = (
        f"Conversation History:\n"
        f"{history_text if history_text else '(No prior conversation history)'}\n\n"
        f"Latest User Question:\n"
        f"\"{clean_q}\"\n\n"
        f"Standalone Question or AMBIGUOUS_CLARIFICATION_REQUIRED:"
    )

    try:
        rewritten = gemini.generate_response(user_prompt, SYSTEM_REWRITE_PROMPT, model_override="gemini-2.5-flash")
        rewritten_clean = rewritten.strip().strip('"').strip("'")
        
        if "AMBIGUOUS_CLARIFICATION_REQUIRED" in rewritten_clean:
            Logger.info(f"Query Rewriter -> Ambiguity unresolvable from history: '{clean_q}'")
            return "AMBIGUOUS_CLARIFICATION_REQUIRED"

        if rewritten_clean and len(rewritten_clean) > 3:
            Logger.info(f"Query Rewriter -> Original: '{clean_q}' | Rewritten: '{rewritten_clean}'")
            return rewritten_clean
    except Exception as e:
        Logger.error(f"Query rewriter error: {e}")
        
    return clean_q


def generate_multi_queries(query: str) -> List[str]:
    """
    Multi-Query Retrieval: generates 2-4 semantically diverse reformulations
    of the original query to maximize retrieval recall across different facets
    (direct rule, exceptions, procedures, penalties).

    Returns a list starting with the original query followed by LLM variants.
    Always returns at least [query] if LLM fails.
    """
    clean_q = query.strip()
    prompt = f"User Query: {clean_q}\n\nGenerate 3 diverse reformulations:"

    try:
        raw = gemini.generate_response(
            prompt, SYSTEM_MULTI_QUERY_PROMPT, model_override="gemini-2.5-flash"
        )
        if not raw:
            return [clean_q]

        # Parse numbered lines: "1. ...", "2. ...", "3. ..."
        variants = []
        for line in raw.strip().split('\n'):
            line = line.strip()
            # Strip leading numbering like "1." or "1)"
            cleaned = re.sub(r'^\d+[.)]\s*', '', line).strip()
            if cleaned and len(cleaned) > 5:
                variants.append(cleaned)

        # Deduplicate and limit to 3 variants
        seen = {clean_q.lower()}
        unique_variants = []
        for v in variants[:3]:
            if v.lower() not in seen:
                seen.add(v.lower())
                unique_variants.append(v)

        all_queries = [clean_q] + unique_variants
        Logger.info(f"Multi-Query Rewriter: {len(all_queries)} queries generated for: '{clean_q[:60]}'")
        for i, q in enumerate(all_queries):
            Logger.info(f"  Query [{i}]: {q}")
        return all_queries

    except Exception as e:
        Logger.error(f"Multi-Query Rewriter failed: {e}. Using original query only.")
        return [clean_q]
