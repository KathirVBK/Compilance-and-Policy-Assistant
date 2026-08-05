import re
from backend.utils.logger import Logger

# Regulatory/Security Compliance trigger terms
ESCALATION_KEYWORDS = [
    'bribe', 'bribery', 'corruption', 'whistleblower', 'lawsuit', 'harassment', 'sue', 
    'illegal', 'prosecute', 'regulatory violation', 'safety hazard', 'public official', 
    'kickback', 'compliance breach', 'legal action', 'insider trading', 'fraud', 'steal',
    'embezzle', 'laundering', 'bribing'
]

GREETING_WORDS = ['hi', 'hello', 'hey', 'greetings', 'who are you', 'how can you help', 'help']

def analyze_intent(query):
    """Intent Agent: Evaluates user query to determine task routing path"""
    Logger.info(f"Intent Agent analyzing query: '{query}'")
    
    clean_query = query.strip().lower()
    
    # 1. Check for high-risk compliance triggers
    triggered = []
    for keyword in ESCALATION_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r's?\b', clean_query):
            triggered.append(keyword)
            
    if triggered:
        Logger.warn(f"High risk compliance term detected: {triggered}")
        return {
            "intent": "escalate",
            "risk_level": "HIGH",
            "details": f"Query contains high-risk terms: {', '.join(triggered)}."
        }
        
    # 2. Check for simple conversational greetings
    if clean_query in GREETING_WORDS or len(clean_query.split()) <= 2 and any(w in clean_query for w in ['hi', 'hello', 'help']):
        return {
            "intent": "greet",
            "risk_level": "LOW",
            "details": "Standard greeting or help prompt."
        }
        
    # 3. Default to RAG retrieval path
    return {
        "intent": "retrieve",
        "risk_level": "LOW",
        "details": "Requires vector database RAG search."
    }
