import os
from backend.config import Config

PROMPT_DIR = os.path.join(Config.BASE_DIR, '..', 'prompts')

def get_system_prompt():
    path = os.path.join(PROMPT_DIR, 'system_prompt.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return "You are an Enterprise Compliance & Operations AI Assistant."

def get_retrieval_prompt():
    path = os.path.join(PROMPT_DIR, 'retrieval_prompt.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Analyze the query for retrieval."

def get_response_prompt(context, query, history=None):
    path = os.path.join(PROMPT_DIR, 'response_prompt.txt')
    history_text = ""
    if history and len(history) > 0:
        history_text = "Recent Conversation History:\n"
        for msg in history[-6:]:
            sender = "User" if msg.get("sender") == "user" else "Assistant"
            text = msg.get("text", "")
            if sender == "Assistant" and len(text) > 250:
                text = text[:250] + "..."
            history_text += f"{sender}: {text}\n"

    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            template = f.read()
            return template.replace("{history}", history_text).replace("{context}", context).replace("{query}", query)
    return f"{history_text}\nRetrieved Policy Context:\n{context}\n\nUser Query:\n{query}"
