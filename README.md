# AI Decision Governance Copilot

An enterprise-grade, agentic workflow system built with **LangGraph**, **Google Gemini**, and **MongoDB**. This system automates and governs AI-driven actions (like refunds or access requests) with multi-agent validation, risk analysis, and human-in-the-loop capabilities.

## 🚀 Key Features

- **Multi-Agent Orchestration:** Specialized agents for Intent, Policy, Memory, Risk, and Audit.
- **Short-Term Memory:** Automatic state checkpointing in MongoDB for fault tolerance and resumption.
- **Long-Term Memory:** Persistent cross-thread knowledge via MongoDBStore to track user history and patterns.
- **Structured Output:** Guaranteed schema validation using Gemini 1.5/2.0 with Pydantic.
- **Human-in-the-Loop:** Built-in escalation paths for manual review of high-risk decisions.

## 🛠️ Tech Stack

- **Orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph)
- **LLM:** Google Gemini 1.5 Pro / Flash
- **Database:** MongoDB (Operational & History)
- **Vector Store:** ChromaDB (Policy RAG)
- **API Framework:** FastAPI
- **Validation:** Pydantic

## 📂 Project Structure

```text
ai-governance-copilot/
├── app/
│   ├── agents/       # Specialized agent logic (intent, risk, etc.)
│   ├── graph/        # LangGraph workflow definition
│   ├── schemas/      # Shared GovernanceState and Pydantic models
│   ├── services/     # LLM, DB, and Persistence services
│   ├── policies/     # Governance policy documents
│   ├── api/          # FastAPI routes
│   └── main.py       # Application entry point
├── tests/            # End-to-end and unit tests
├── .env.example      # Template for environment variables
└── README.md
```

## ⚙️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd ai-governance-copilot
   ```

2. **Set up Environment Variables:**
   Create a `.env` file based on the keys in `.env.example`:
   ```env
   GOOGLE_API_KEY=your_key_here
   MONGODB_URI=your_mongodb_uri
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Running Tests

To run a sample end-to-end request (requires API keys):
```bash
# Note: Ensure you are in the root directory
python tests/run_sample.py
```

## 📄 License

This project is licensed under the MIT License.
