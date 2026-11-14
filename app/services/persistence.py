"""
Persistence Service
════════════════════
Initialises both LangGraph persistence backends backed by MongoDB:

1. MongoDBSaver (checkpointer) → short-term, thread-scoped state snapshots
2. MongoDBStore (store)         → long-term, cross-thread memory

Both connect to the same MongoDB database defined in .env.
"""

from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.store.mongodb import MongoDBStore

from app.config import MONGODB_URI, MONGODB_DB_NAME


try:
    import certifi
    ca_file = certifi.where()
except ImportError:
    ca_file = None

# ── MongoDB Client ───────────────────────────────────────────────

client_kwargs = {"tlsCAFile": ca_file} if ca_file else {}
client = MongoClient(MONGODB_URI, **client_kwargs)


# ── Short-Term Memory (Checkpointer) ────────────────────────────
# Automatically snapshots GovernanceState after every agent node.
# Collections created: `checkpoints` + `checkpoint_writes`

checkpointer = MongoDBSaver(client, db_name=MONGODB_DB_NAME)


# ── Long-Term Memory (Store) ────────────────────────────────────
# Cross-thread storage for past decisions, risk patterns, audit logs.
# Collection: `memories`
# Note: use direct constructor with shared client (from_conn_string is a
# context manager and cannot be used for module-level singletons).

store = MongoDBStore(
    collection=client[MONGODB_DB_NAME]["memories"],
)
