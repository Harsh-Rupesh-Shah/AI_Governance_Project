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


# ── MongoDB Client ───────────────────────────────────────────────

client = MongoClient(MONGODB_URI)


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
