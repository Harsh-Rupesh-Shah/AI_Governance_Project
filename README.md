# AI Decision Governance Copilot

An enterprise-grade, agentic governance and decision verification system built with **LangGraph**, **Google Gemini**, **MongoDB Atlas**, **ChromaDB**, **FastAPI**, and **React**. 

The system automates and governs AI-driven actions (such as high-value refunds, access escalations, and policy checks) with multi-agent validation, deterministic guardrails, long-term memory, contextual risk analysis, and interactive human-in-the-loop clarification.

---

## 🚀 Key Features

- **Multi-Agent Governance Workflow**:
  - `intent_agent`: Structured intent & entity extraction via Google Gemini using strict Pydantic schemas.
  - `policy_agent`: Vector RAG powered by ChromaDB retrieving relevant enterprise policy rules.
  - `memory_agent`: Cross-thread historical memory backed by MongoDB Store tracking previous customer incidents.
  - `risk_agent`: Hybrid risk engine combining deterministic policy rules with contextual LLM reasoning.
  - `decision_agent`: Enforces deterministic policy guardrails (`APPROVE`, `DENY`, `ESCALATE`, `CLARIFY`).
  - `audit_agent`: Writes tamper-evident, permanent audit ledger records into MongoDB Atlas.
- **Resilient Multi-Tier LLM Architecture**:
  - Powered by high-quota Google Gemini models (1,500 requests/day).
  - Built-in multi-key and model fallback (`gemini-2.5-flash` $\rightarrow$ backup key $\rightarrow$ `gemini-1.5-flash`) via LangChain's native `.with_fallbacks()` for zero-downtime execution.
- **Interactive Human-in-the-Loop (`CLARIFY`)**:
  - When requests lack mandatory details or justifications, the copilot automatically halts in a `CLARIFY` state, prompts the user, and seamlessly resumes with preserved state.
- **Full-Stack Experience**:
  - Interactive terminal CLI for rapid development and testing.
  - Modern FastAPI backend with JWT authentication and state inspection endpoints.
  - Interactive React/Vite dashboard with live workflow X-Ray telemetry and audit ledger review.

---

## 🛠️ Tech Stack

- **Workflow Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph) (StateGraph, checkpointing, and store)
- **Language Models**: Google Gemini (`gemini-2.5-flash` / `gemini-1.5-flash`) via `langchain-google-genai`
- **Vector Database**: ChromaDB via `langchain-chroma` & local HuggingFace embeddings (`all-MiniLM-L6-v2`)
- **Operational & State Store**: MongoDB Atlas via `langgraph-checkpoint-mongodb` and `langgraph-store-mongodb`
- **Backend API**: FastAPI, Uvicorn, Pydantic v2
- **Frontend Dashboard**: React 18, TypeScript, Tailwind CSS, Lucide icons, Vite

---

## 📂 Project Structure

```text
AI_Governance_Project/
├── app/
│   ├── agents/           # Specialized agent nodes (intent, policy, memory, risk, decision, audit)
│   ├── api/              # FastAPI endpoints (auth, governance, audit)
│   ├── config.py         # Centralized environment configuration
│   ├── graph/            # LangGraph StateGraph workflow definition
│   ├── policies/         # Markdown governance policy documents (e.g., refund_policy.md)
│   ├── schemas/          # Pydantic models and GovernanceState definition
│   ├── services/         # LLM service, ChromaDB vector store, MongoDB persistence
│   └── main.py           # FastAPI application entry point
├── cli_script/
│   ├── clear_db.py       # Utility to clear test sessions and memories in MongoDB
│   └── run_interactive.py# Interactive CLI copilot interface
├── frontend/             # React + Vite web dashboard
│   ├── src/
│   │   ├── components/   # UI components, layout, and protected route wrapper
│   │   ├── pages/        # Login, Workspace (Copilot X-Ray), and Audit Ledger
│   │   └── services/     # API client and auth tokens
│   └── package.json
├── tests/                # Automated test suites (unit, integration, resilience)
│   ├── test_all_features.py
│   ├── test_resilient_llm.py
│   └── test_upgrades.py
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.11+ (tested on Python 3.14)
- Node.js 18+ (for frontend)
- MongoDB Atlas account (or local MongoDB 6+)
- Google AI Studio API key

### 2. Clone and Prepare Virtual Environment
```bash
git clone https://github.com/Harsh-Rupesh-Shah/AI_Governance_Project.git
cd AI_Governance_Project

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```
Key variables:
```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_API_KEY_BACKUP=optional_backup_gemini_key
GOOGLE_MODEL=gemini-2.5-flash
GOOGLE_FALLBACK_MODEL=gemini-1.5-flash

MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?appName=AIGovernance
MONGODB_DB_NAME=ai_governance

CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=governance_policies
```

---

## 🚀 Running the Application

### 1. Ingest Governance Policies into ChromaDB
Before running queries, index the policy files (`app/policies/`) into the local Chroma vector store:
```bash
python app/services/vectordb.py
```
*(Outputs: `Successfully ingested 139 policy chunks into ChromaDB.`)*

### 2. Run the Interactive CLI Copilot
For rapid testing in the terminal:
```bash
python cli_script/run_interactive.py
```
Type governance requests such as:
- `Please refund 75,000 INR to customer CUST-8872` (Triggers threshold and historical risk escalation)
- `Please refund 300 INR to customer CUST-1001 for a damaged book` (Auto-approves)
- `I want a refund` (Triggers clarification loop)

### 3. Launch the Full-Stack Dashboard
Run the FastAPI backend:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In a separate terminal, start the frontend development server:
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 🧪 Running Automated Tests

Run the complete test suite (26 unit, integration, and resilience tests):
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 License

This project is licensed under the MIT License.
