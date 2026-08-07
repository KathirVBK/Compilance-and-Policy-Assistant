const API_BASE = "http://localhost:3000/api";

export const api = {
  async getModels() {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) throw new Error("Failed to fetch models");
    return res.json();
  },

  async queryAgent(query, model, history = [], sessionId = null, targetDoc = null) {
    const res = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, model, history, session_id: sessionId, target_doc: targetDoc })
    });
    if (!res.ok) throw new Error("Failed to process query");
    return res.json();
  },

  async getDocuments() {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error("Failed to fetch documents");
    return res.json();
  },

  async deleteDocument(title) {
    const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(title)}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to delete document");
    return res.json();
  },

  async uploadDocument(formData) {
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to upload document");
    }
    return res.json();
  },

  async transcribeSpeech(audioBlob) {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");
    
    const res = await fetch(`${API_BASE}/speech/transcribe`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) throw new Error("Failed to transcribe audio");
    return res.json();
  },

  async synthesizeSpeech(text) {
    const res = await fetch(`${API_BASE}/speech/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error("Failed to synthesize speech");
    return res.blob();
  },

  async resetDatabase() {
    const res = await fetch(`${API_BASE}/reset`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Failed to reset database");
    return res.json();
  }
};
