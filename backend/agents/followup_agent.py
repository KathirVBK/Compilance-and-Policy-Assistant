from typing import List, Dict
from backend.llm import gemini
from backend.utils.logger import Logger

SYSTEM_FOLLOWUP_PROMPT = (
    "You are a Proactive Compliance Assistant. Given the user query, generated answer, and retrieved policy section metadata, "
    "generate 2-3 highly relevant, self-contained follow-up questions an employee might ask next.\n\n"
    "STRICT GROUNDING & QUALITY RULES:\n"
    "1. GROUNDED IN RETRIEVED SECTIONS: Base suggestions directly on adjacent topics, procedures, exceptions, or parameters "
    "mentioned in the retrieved policy context (e.g., if context covers PTO accrual, suggest maximum carryover caps or payout upon resignation; "
    "if FMLA, suggest intermittent leave rules or comparison to personal days).\n"
    "2. SELF-CONTAINED QUESTIONS: Ensure every suggested question is explicit and self-contained so it can be queried directly "
    "(e.g., write 'What is the maximum PTO carryover cap?' instead of 'What about carryover?').\n"
    "3. OUTPUT FORMAT: Output ONLY 2 to 3 bullet points starting with '• '.\n"
    "Example:\n"
    "• How does FMLA leave compare to standard personal days?\n"
    "• What is the maximum carryover balance allowed at year-end?\n"
    "• What notice period is required before taking scheduled PTO?"
)

def generate_followup_suggestions(query: str, answer: str, retrieved_chunks: List[Dict[str, str]] = None) -> List[str]:
    """
    Generates 2-3 grounded, self-contained follow-up questions based on answer & chunk metadata.
    """
    if not retrieved_chunks or len(retrieved_chunks) == 0:
        return [
            "What are the Paid Time Off (PTO) accrual rates?",
            "How much notice is required for resignation?",
            "What personal days are full-time employees entitled to?"
        ]

    # Extract sections & snippet summary from chunks
    sections = set()
    chunk_snippets = ""
    for c in retrieved_chunks[:3]:
        sec = c.get('section') or 'General Policy'
        sections.add(sec)
        chunk_snippets += f"Section [{sec}]: {c.get('content', '')[:200]}\n"

    sections_str = ", ".join(list(sections))

    user_prompt = (
        f"User Query: {query}\n"
        f"Retrieved Policy Sections: {sections_str}\n"
        f"Retrieved Context Snippets:\n{chunk_snippets}\n"
        f"Generated Answer Preview: {answer[:300]}...\n\n"
        f"Grounded Follow-up Questions:"
    )

    try:
        raw_output = gemini.generate_response(user_prompt, SYSTEM_FOLLOWUP_PROMPT, model_override="gemini-2.5-flash")
        lines = raw_output.strip().split('\n')
        
        followups = []
        for line in lines:
            clean_q = line.strip().lstrip('•-*123456789. ').strip()
            if clean_q and len(clean_q) > 10 and clean_q.endswith('?'):
                followups.append(clean_q)
                
        if len(followups) >= 2:
            Logger.info(f"Followup Agent generated {len(followups)} grounded follow-up questions for sections: {sections_str}")
            return followups[:3]
    except Exception as e:
        Logger.error(f"Followup Agent error: {e}")

    # Default grounded fallback questions
    return [
        "What is the maximum PTO accrual balance allowed?",
        "How do I submit a formal leave request?",
        "What notice period is required for scheduled absences?"
    ]
