let API_BASE = import.meta.env.VITE_API_URL || "http://localhost:3000/api";

// Auto-correct common deployment misconfigurations (e.g., adding :3000 or using http on Render)
if (API_BASE.includes("onrender.com")) {
  API_BASE = API_BASE.replace(/:\d+(?=\/|$)/, "");
  if (API_BASE.startsWith("http://")) {
    API_BASE = API_BASE.replace("http://", "https://");
  }
}

// ─── Auth token helpers ───────────────────────────────────────────────────────
const getToken  = () => localStorage.getItem("pb_token") || "";
const getUser   = () => {
  try { return JSON.parse(localStorage.getItem("pb_user") || "null"); } catch { return null; }
};
const authHeader = () => ({ Authorization: `Bearer ${getToken()}` });

const customFetch = async (url, options) => {
  const res = await fetch(url, options);
  if (res.status === 401) {
    window.dispatchEvent(new Event("auth:unauthorized"));
  }
  return res;
};

// ─── API Service ──────────────────────────────────────────────────────────────
export const api = {
  // ── Auth ────────────────────────────────────────────────────────────────────
  async login(username, password) {
    const res = await customFetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("pb_token", data.token);
    localStorage.setItem("pb_user",  JSON.stringify(data.user));
    return data;
  },

  async register(username, password, name, email) {
    const res = await customFetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, name, email })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    return res.json();
  },

  async logout() {
    try {
      await customFetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: authHeader()
      });
    } catch { /* ignore network errors on logout */ }
    localStorage.removeItem("pb_token");
    localStorage.removeItem("pb_user");
  },

  async getMe() {
    const res = await customFetch(`${API_BASE}/auth/me`, { headers: authHeader() });
    if (!res.ok) throw new Error("Not authenticated");
    return res.json();
  },

  async getRoles() {
    const res = await customFetch(`${API_BASE}/auth/roles`, { headers: authHeader() });
    if (!res.ok) throw new Error("Failed to fetch roles");
    return res.json();
  },

  getCurrentUser: getUser,
  getToken,

  // ── Models ──────────────────────────────────────────────────────────────────
  async getModels() {
    const res = await customFetch(`${API_BASE}/models`, { headers: authHeader() });
    if (!res.ok) throw new Error("Failed to fetch models");
    return res.json();
  },

  // ── Query ───────────────────────────────────────────────────────────────────
  async queryAgent(query, model, history = [], sessionId = null, targetDoc = null) {
    const user = getUser();
    const res = await customFetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({
        query,
        model,
        history,
        session_id: sessionId,
        target_doc: targetDoc,
        user_role:  user?.role || "employee"
      })
    });
    if (!res.ok) throw new Error("Failed to process query");
    return res.json();
  },

  // ── Documents ───────────────────────────────────────────────────────────────
  async getDocuments(category = null, tag = null) {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (tag)      params.append("tag", tag);
    const qs  = params.toString() ? `?${params}` : "";
    const res = await customFetch(`${API_BASE}/documents${qs}`, { headers: authHeader() });
    if (!res.ok) throw new Error("Failed to fetch documents");
    return res.json();
  },

  async deleteDocument(title) {
    const res = await customFetch(`${API_BASE}/documents/${encodeURIComponent(title)}`, {
      method: "DELETE",
      headers: authHeader()
    });
    if (!res.ok) throw new Error("Failed to delete document");
    return res.json();
  },

  async getCategories() {
    const res = await customFetch(`${API_BASE}/categories`, { headers: authHeader() });
    if (!res.ok) throw new Error("Failed to fetch categories");
    return res.json();
  },

  // ── Upload ──────────────────────────────────────────────────────────────────
  async uploadDocument(formData) {
    const res = await customFetch(`${API_BASE}/upload`, {
      method: "POST",
      headers: authHeader(),   // No Content-Type: let browser set multipart boundary
      body: formData
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Failed to upload document");
    }
    return res.json();
  },

  // ── Speech ──────────────────────────────────────────────────────────────────
  async transcribeSpeech(audioBlob) {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");
    const res = await customFetch(`${API_BASE}/speech/transcribe`, {
      method: "POST",
      headers: authHeader(),
      body: formData
    });
    if (!res.ok) throw new Error("Failed to transcribe audio");
    return res.json();
  },

  async synthesizeSpeech(text) {
    const res = await customFetch(`${API_BASE}/speech/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error("Failed to synthesize speech");
    return res.blob();
  },

  // ── Reset ───────────────────────────────────────────────────────────────────
  async resetDatabase() {
    const res = await customFetch(`${API_BASE}/reset`, {
      method: "POST",
      headers: authHeader()
    });
    if (!res.ok) throw new Error("Failed to reset database");
    return res.json();
  },

  // ── Admin ───────────────────────────────────────────────────────────────────
  async getUsers() {
    const res = await customFetch(`${API_BASE}/admin/users`, { headers: authHeader() });
    if (!res.ok) throw new Error("Failed to fetch users");
    return res.json();
  },

  async createUser(data) {
    const res = await customFetch(`${API_BASE}/admin/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create user");
    }
    return res.json();
  },

  async deleteUser(username) {
    const res = await customFetch(`${API_BASE}/admin/users/${encodeURIComponent(username)}`, {
      method: "DELETE",
      headers: authHeader()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to delete user");
    }
    return res.json();
  },

  async updateUserRole(username, role) {
    const res = await customFetch(`${API_BASE}/admin/users/${encodeURIComponent(username)}/role`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({ role })
    });
    if (!res.ok) throw new Error("Failed to update role");
    return res.json();
  },

  async getAuditLog(limit = 200, severity = null) {
    const params = new URLSearchParams({ limit });
    if (severity) params.append("severity", severity);
    const res = await customFetch(`${API_BASE}/admin/audit-log?${params}`, { headers: authHeader() });
    if (!res.ok) throw new Error("Failed to fetch audit log");
    return res.json();
  },

  async clearAuditLog() {
    const res = await customFetch(`${API_BASE}/admin/audit-log`, {
      method: "DELETE",
      headers: authHeader()
    });
    if (!res.ok) throw new Error("Failed to clear audit log");
    return res.json();
  },

  async getAdminStats() {
    const res = await customFetch(`${API_BASE}/admin/stats`, { headers: authHeader() });
    if (!res.ok) throw new Error("Failed to fetch stats");
    return res.json();
  },

  async updateDocRoles(docTitle, allowedRoles) {
    const res = await customFetch(`${API_BASE}/admin/documents/${encodeURIComponent(docTitle)}/roles`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({ allowed_roles: allowedRoles })
    });
    if (!res.ok) throw new Error("Failed to update document roles");
    return res.json();
  },

  async updateDocTags(docTitle, tags) {
    const res = await customFetch(`${API_BASE}/admin/documents/${encodeURIComponent(docTitle)}/tags`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({ tags })
    });
    if (!res.ok) throw new Error("Failed to update document tags");
    return res.json();
  }
};
