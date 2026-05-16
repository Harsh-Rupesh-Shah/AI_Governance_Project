"""
Policy Retrieval Agent (RAG)
════════════════════════════
Retrieves relevant governance policies from the vector store
using semantic search over ChromaDB.

Input from state:  request_text, action_type, risk_category
Writes to state:   retrieved_policies, matched_policy_ids
"""

from app.schemas.models import GovernanceState


def policy_agent(state: GovernanceState) -> dict:
    """
    LangGraph node: retrieve relevant policies via RAG.
    TODO: Implement ChromaDB semantic search.
    """
    return {
        "retrieved_policies": [],
        "matched_policy_ids": [],
    }
