from backend.graph.state import AgentState
from backend.agents import intent_agent, retrieval_agent, response_agent, query_rewriter
from backend.utils.session_manager import SessionManager
from backend.utils.logger import Logger

class ComplianceGraph:
    def __init__(self):
        pass

    def execute(self, state: AgentState) -> AgentState:
        """Executes the sequential multi-agent graph nodes with session history management"""
        session_id = SessionManager.get_or_create_session(state.session_id)
        state.session_id = session_id

        # Retrieve backend session history if not explicitly provided
        history = state.history if state.history is not None else SessionManager.get_session_history(session_id)

        # Multi-turn: prepend rolling summary as a synthetic context message if one exists
        session_summary = SessionManager.get_session_summary(session_id)
        if session_summary and (not history or history[0].get("_is_summary") is None):
            history = [{"sender": "assistant", "text": f"[Session Summary] {session_summary}", "_is_summary": True}] + list(history)

        state.history = history

        Logger.info(f"Starting Graph Execution for Session [{session_id[:8]}] | Role: '{state.user_role}' | Query: '{state.query}'")

        # Node 0: Query Contextualization / Rewriting (Pass History)
        state.rewritten_query = query_rewriter.rewrite_query(state.query, history)

        # Check if rewriter detected unresolvable ambiguity (no history to resolve pronoun)
        if state.rewritten_query == "AMBIGUOUS_CLARIFICATION_REQUIRED":
            Logger.info(f"Ambiguity detected without history context for: '{state.query}'")
            state.response = {
                "status": "clarify",
                "query": state.query,
                "session_id": session_id,
                "model": state.model_override or "gemini-2.5-flash",
                "answer": (
                    "Could you please clarify which specific policy or topic you would like details on? "
                    "(e.g., Paid Time Off accruals, Bereavement Leave, FMLA guidelines, or Resignation Notice rules)\n\n"
                    "• PTO Accrual & Annual Limits\n"
                    "• Bereavement & Personal Days\n"
                    "• FMLA Eligibility & Duration\n"
                    "• Resignation Notice Guidelines"
                ),
                "citations": [],
                "verification": {
                    "completeness": "Requested topic clarification from user",
                    "conflicts": "No conflicts detected",
                    "currency": "Active session",
                    "riskLevel": "LOW"
                },
                "steps": [
                    {
                        "step": "Stage 1: Query Contextualizer (LLM Call 1)",
                        "desc": "Ambiguous reference detected without prior conversation context. Requested topic clarification."
                    }
                ]
            }
            SessionManager.add_turn(session_id, state.query, state.response["answer"])
            return state

        if state.rewritten_query != state.query:
            Logger.info(f"Query Contextualized -> Original: '{state.query}' | Standalone: '{state.rewritten_query}'")

        target_query = state.rewritten_query or state.query

        # Node 1: Intent Analysis
        intent_results = intent_agent.analyze_intent(target_query)
        state.intent = intent_results

        # Conditional Edge Routing
        if intent_results["intent"] in ["escalate", "greet"]:
            Logger.info(f"Routing query directly to response node (Intent: {intent_results['intent']})")
            state.retrieved_chunks = []
        else:
            # Node 2: Document Retrieval — Multi-Query + Reranking + Parent Expand
            Logger.info(f"Routing standalone query '{target_query}' to advanced retrieval node (Target Doc: {state.target_doc}, Role: {state.user_role}).")
            chunks = retrieval_agent.retrieve_context(
                target_query,
                target_doc=state.target_doc,
                user_role=state.user_role
            )
            state.retrieved_chunks = chunks

        # Node 3: Response Generation (Pass History separately from retrieval)
        response = response_agent.generate_answer(
            query=state.query,
            intent_results=state.intent,
            retrieved_chunks=state.retrieved_chunks,
            model_override=state.model_override,
            history=history
        )

        # Append Two-Stage Architecture steps to execution trace logs
        if response and "steps" in response:
            rewrite_desc = (
                f"Rewrote query into standalone + generated 2-4 multi-query variants: '{target_query}'"
                if state.rewritten_query != state.query
                else f"Input query is standalone: '{state.query}'. Generated 2-4 multi-query variants."
            )
            response["steps"].insert(0, {
                "step": "Stage 1: Query Contextualizer + Multi-Query Generator (LLM Call 1)",
                "desc": rewrite_desc
            })

        # Store completed conversation turn into SessionManager
        if response and "answer" in response:
            response["session_id"] = session_id
            SessionManager.add_turn(session_id, state.query, response["answer"])

        state.response = response

        Logger.info("Graph Execution Completed.")
        return state


# Singleton instance
graph = ComplianceGraph()


def run_workflow(query, model=None, history=None, session_id=None, target_doc=None, user_role=None):
    """Entry point to run the agent graph workflow"""
    state = AgentState(
        query=query,
        model_override=model,
        history=history,
        session_id=session_id,
        target_doc=target_doc,
        user_role=user_role or "employee"
    )
    final_state = graph.execute(state)
    return final_state.response
