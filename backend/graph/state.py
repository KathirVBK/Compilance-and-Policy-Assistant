from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AgentState(BaseModel):
    query: str
    session_id: Optional[str] = None
    rewritten_query: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    intent: Optional[Dict[str, Any]] = None
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None
    response: Optional[Dict[str, Any]] = None
    model_override: Optional[str] = None
    target_doc: Optional[str] = None
