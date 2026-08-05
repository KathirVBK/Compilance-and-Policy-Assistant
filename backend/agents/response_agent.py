from backend.llm import gemini, prompts
from backend.utils.logger import Logger

def generate_answer(query, intent_results, retrieved_chunks, model_override=None, history=None):
    """Response Agent: Formulates the final compliance response and audit report"""
    Logger.info("Response Agent generating final compliance output.")
    
    # 1. Check for immediate escalation
    if intent_results["intent"] == "escalate":
        return {
            "status": "escalated",
            "query": query,
            "model": model_override or "gemini-2.5-flash",
            "answer": (
                "⚠️ **Compliance Escalation Warning**: Your query contains terms related to high-risk legal/ethical violations. "
                "In accordance with corporate compliance guidelines, this query has been automatically logged and routed to "
                "the Human Legal & Compliance Department.\n\n"
                "For your reference, Endeavors enforces a zero-tolerance policy towards fraud, bribery, corruption, "
                "or retaliation. Please contact the Corporate Compliance Officer immediately for formal counsel."
            ),
            "citations": [],
            "verification": {
                "completeness": "Escalated for immediate human intervention",
                "conflicts": "Not evaluated",
                "currency": "Urgent compliance warning raised",
                "riskLevel": "HIGH RISK"
            },
            "steps": [
                {"step": "Analyze Query", "desc": "Analyzed query and triggered high-risk compliance keywords check."},
                {"step": "Escalation Route", "desc": "Triggered direct escalation routing to compliance helpdesk."}
            ]
        }

    # 2. Check for simple greetings
    if intent_results["intent"] == "greet":
        return {
            "status": "success",
            "query": query,
            "model": model_override or "gemini-2.5-flash",
            "answer": (
                "Hello! I am your Enterprise Compliance & Operations AI Assistant. I can help search the "
                "corporate employee handbooks (such as `handbook_2025`), explain policies, and check regulations.\n\n"
                "How can I help you today? (e.g. ask about dress code, resignation notice, or PTO accrual rates)"
            ),
            "citations": [],
            "verification": {
                "completeness": "Conversational greeting handled",
                "conflicts": "No conflicts detected",
                "currency": "Current session active",
                "riskLevel": "LOW"
            },
            "steps": [
                {"step": "Analyze Query", "desc": "Identified query as a conversational greeting."},
                {"step": "Greeting Output", "desc": "Returned standard greeting guidelines."}
            ]
        }

    # 3. Check for empty retrieval context
    if not retrieved_chunks:
        return {
            "status": "clarify",
            "query": query,
            "model": model_override or "gemini-2.5-flash",
            "answer": (
                "ℹ️ **No Relevant Policy Content Found**: No matching company policy documents or sections "
                "were found in the knowledge base above the relevance threshold for your query.\n\n"
                "Please verify whether this topic is covered under official employee handbooks, or try rephrasing your question with specific terms."
            ),
            "citations": [],
            "verification": {
                "completeness": "No relevant policy content found above similarity threshold",
                "conflicts": "No conflicts detected",
                "currency": "N/A",
                "riskLevel": "LOW"
            },
            "steps": [
                {"step": "Analyze Query", "desc": "Analyzed query for policy search extraction."},
                {"step": "RAG Retrieval", "desc": "FAISS database search yielded zero matches above similarity floor threshold."}
            ]
        }

    # 4. Formulate Prompt & Call LLM with Audit Traceability
    context_text = ""
    for idx, chunk in enumerate(retrieved_chunks):
        chunk_id = chunk.get('id', f'chunk_{idx}')
        doc_title = chunk.get('docTitle', 'Document')
        section_name = chunk.get('section') or 'General'
        page_num = chunk.get('page', 1)
        
        # Log underlying chunk traceability mapping for auditing
        Logger.info(f"Citation Traceability -> ID: {chunk_id} | Doc: '{doc_title}' | Section: '{section_name}' | Page: {page_num}")
        
        context_text += (
            f"Source [{idx+1}] - Doc: {doc_title} (v{chunk.get('version', '1.0')}, Date: {chunk.get('date', '2025-01-01')}) "
            f"| Section: \"{section_name}\" | Page: {page_num}:\n{chunk.get('content', '')}\n\n"
        )

    system_instruction = prompts.get_system_prompt()
    user_prompt = prompts.get_response_prompt(context_text, query, history)

    llm_response = gemini.generate_response(user_prompt, system_instruction, model_override)
    
    # Strip all source markers, inline [Source X] references, and trailing source blocks
    import re
    llm_response = re.sub(r'\n+\*?\s*(?:Source|Sources|References|Based on the Employee Handbook|Based on the provided sources)[^\n]*.*$', '', llm_response, flags=re.IGNORECASE | re.DOTALL).strip()
    llm_response = re.sub(r'\*?\s*Source:\s*.*$', '', llm_response, flags=re.IGNORECASE | re.DOTALL).strip()
    llm_response = re.sub(r'\[?\bSource\s*\[?\d+\]?\]?:?', '', llm_response, flags=re.IGNORECASE).strip()
    llm_response = re.sub(r'\[\d+\]', '', llm_response).strip()
    llm_response = re.sub(r'\(\s*\)', '', llm_response).strip()
    llm_response = re.sub(r'\*\s*\(\s*$', '', llm_response).strip()
    
    # Strip any opening source preamble phrases (e.g. "Based on the provided context,", "According to the handbook,")
    llm_response = re.sub(r'^(?:Based on the (?:provided|retrieved|official|Employee) (?:context|policy|sources|handbook|documents?)[,\s]*|According to the (?:employee )?handbook[,\s]*|\(Endeavors\)\s*v?\d*\.?\d*,?\s*)+', '', llm_response, flags=re.IGNORECASE).strip()
    if llm_response and llm_response[0].islower():
        llm_response = llm_response[0].upper() + llm_response[1:]

    # Remove all raw asterisks (*) to eliminate AI-generated raw markdown look
    llm_response = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', llm_response)
    llm_response = re.sub(r'^\s*[*]\s+', '• ', llm_response, flags=re.MULTILINE)
    llm_response = llm_response.replace('*', '')

    # Generate metadata-grounded follow-up suggestions
    from backend.agents import followup_agent
    followups = followup_agent.generate_followup_suggestions(query, llm_response, retrieved_chunks)
    if followups and len(followups) > 0:
        llm_response += "\n\nFollow-up Questions:\n" + "\n".join([f"• {q}" for q in followups])

    # 5. Execute Compliance Audit checks on citations
    steps = [
        {"step": "Stage 2: FAISS Vector Retrieval", "desc": f"Retrieved {len(retrieved_chunks)} matching context blocks from FAISS store."},
        {"step": "Stage 3: Answer Generation (LLM Call 2)", "desc": "Formulated final compliance response using retrieved chunks + history + original query."},
        {"step": "Stage 4: Grounded Follow-up Generator", "desc": f"Generated {len(followups)} grounded follow-up inquiries anchored to retrieved section metadata."}
    ]

    # Conflict Check: checks if different versions of same document exist in citations
    grouped_docs = {}
    for chunk in retrieved_chunks:
        title = chunk['docTitle']
        version = chunk['version']
        if title not in grouped_docs:
            grouped_docs[title] = set()
        grouped_docs[title].add(version)
        
    has_conflicts = any(len(versions) > 1 for versions in grouped_docs.values())
    conflict_desc = "No conflicts detected"
    status = "success"
    
    if has_conflicts:
        status = "conflict"
        conflict_desc = "Contradiction found: Multiple versions of same handbook retrieved"
        steps.append({"step": "Conflict Flagged", "desc": conflict_desc, "status": "warning"})

    # Currency Check: check if effective date is prior to 2024
    is_outdated = False
    for chunk in retrieved_chunks:
        try:
            year = int(chunk['date'].split('-')[0])
            if year < 2024:
                is_outdated = True
        except:
            pass
            
    currency_desc = "Policy is current (latest version)"
    if is_outdated:
        currency_desc = "Warning: Archived/older policy chunk referenced in citations"
        steps.append({"step": "Currency Flagged", "desc": currency_desc, "status": "warning"})

    # Completeness Check: checks for unfulfilled cross-references in text
    is_incomplete = False
    for chunk in retrieved_chunks:
        if "refer to" in chunk['content'].lower() or "see policy" in chunk['content'].lower():
            is_incomplete = True
            
    completeness_desc = "Complete context found"
    if is_incomplete:
        completeness_desc = "Details might be incomplete (references another external document)"
        steps.append({"step": "Cross-Reference Alert", "desc": "Policy mentions secondary references. Please verify details.", "status": "warning"})

    risk_level = "LOW"
    if has_conflicts or is_outdated:
        risk_level = "MEDIUM RISK"

    return {
        "status": status,
        "query": query,
        "model": model_override or "gemini-2.5-flash",
        "answer": llm_response,
        "citations": retrieved_chunks,
        "verification": {
            "completeness": completeness_desc,
            "conflicts": conflict_desc,
            "currency": currency_desc,
            "riskLevel": risk_level
        },
        "steps": steps
    }
