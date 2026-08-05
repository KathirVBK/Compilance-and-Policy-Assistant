# Enterprise Compliance & Operations AI Assistant

A high-fidelity, production-grade prototype for an intelligent AI agent designed to navigate complex, outdated, and conflicting corporate policy documents. 

## Features
- **Conversational Interface**: Dual text/speech interaction with a visual audio wave visualizer.
- **Agent Decision Router**: Automatically flags compliance risks, handles information gaps, detects policy version contradictions, and escalates safety/legal threats.
- **Explainability Panel**: Direct audit logs mapping steps, trust scorecards, and clickable citations.
- **Policy Document Center**: Upload, delete, and view active documents, with single-click DB reset.
- **Allowlisted Model Support**: Supports choosing from allowlisted models like `gemini-2.5-flash` or `gpt-4.1-nano`.

---

## Directory Structure
```text
├── backend/
│   ├── data/                 # JSON Database store
│   ├── uploads/              # Temp upload file directory
│   ├── server.js             # Express API server
│   ├── documentManager.js    # Policy indexing and chunking
│   ├── ragEngine.js          # Retrieval & Conflict evaluation
│   ├── agentCore.js          # Core decision loop & LLM orchestration
│   ├── testAgent.js          # Automated backend test suite
│   └── package.json          # Node dependencies
├── frontend/
│   ├── index.html            # Dashboard structure
│   ├── styles.css            # Dark mode glassmorphism styles
│   └── app.js                # Frontend client controller
└── .env                      # API Configuration
```

---

## Getting Started

### 1. Prerequisites
- [Node.js](https://nodejs.org) (v18+ recommended)

### 2. Installation
Navigate into the `backend/` folder and install the dependencies:
```bash
cd backend
npm install
```

### 3. API Key Integration (Optional)
If you wish to run the assistant with a live LLM instead of the simulated rules engine, open the `.env` file in the root workspace directory and configure your credentials:
```env
API_KEY=your_real_api_key_here
BASE_URL=https://api.openai.com/v1     # Or custom LLM proxy endpoint
SELECTED_MODEL=gemini-2.5-flash
```

---

## Operational Commands

### Run Automated Tests
Verify backend compliance checks and agent routing scenarios:
```bash
cd backend
npm test
```

### Start the Server
Launch the application locally:
```bash
cd backend
npm start
```
Once started, open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## Simulated Test Scenarios

To see the assistant's edge-case handling, ask these questions:
1. **Version Conflict Check**:
   - *Query*: `What is the travel meal allowance limit?`
   - *Result*: The agent identifies two versions of the Travel policy (2024 vs 2026), highlights the contradiction, flags a warning, and prioritizes the newest document version.
2. **Information Stitching**:
   - *Query*: `What are the remote work core hours and my home office equipment stipend?`
   - *Result*: The agent reads the Remote Work guidelines, recognizes it references the "IT Hardware Allocation Policy", retrieves the second policy automatically, and combines the two for a comprehensive response.
3. **Legal Compliance Escalation**:
   - *Query*: `Can I offer a cash gift to a public official to speed up a permit?`
   - *Result*: The agent detects high-risk keywords ("public official", "gift"), raises a "HIGH RISK" alert, details safety rules, and routes the ticket to the Human Compliance Helpdesk.
