from pathlib import Path
import os
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ── LLM Configuration (Morning Digest 1500 req/day Tier) ──────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_API_KEY_BACKUP = os.getenv("GOOGLE_API_KEY_BACKUP", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
GOOGLE_FALLBACK_MODEL = os.getenv("GOOGLE_FALLBACK_MODEL", "gemini-1.5-flash")

# ── MongoDB ──────────────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ai_governance")

# ── ChromaDB ─────────────────────────────────────────────────────
_chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
if not os.path.isabs(_chroma_dir):
    CHROMA_PERSIST_DIR = str((ENV_PATH.parent / _chroma_dir).resolve())
else:
    CHROMA_PERSIST_DIR = _chroma_dir

CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "governance_policies")

# ── FastAPI ──────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
