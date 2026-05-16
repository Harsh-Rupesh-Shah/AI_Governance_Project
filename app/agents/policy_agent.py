"""
Policy Retrieval Agent (RAG)
════════════════════════════
Retrieves relevant governance policies from the vector store
using semantic search over ChromaDB.

Input from state:  request_text, action_type, risk_category
Writes to state:   retrieved_policies, matched_policy_ids
"""

from app.schemas.models import GovernanceState
from app.services.vectordb import retrieve_relevant_policies


def policy_agent(state: GovernanceState) -> dict:
    """
    LangGraph node: retrieve relevant policies via RAG.
    Queries the ChromaDB vector store based on the user's request.
    """
    # Create a query that combines the raw text and the extracted intent
    query_parts = []
    if state.get("action_type"):
        query_parts.append(f"Action: {state['action_type']}")
    if state.get("risk_category"):
        query_parts.append(f"Risk: {state['risk_category']}")
    
    query_parts.append(state["request_text"])
    
    search_query = " | ".join(query_parts)
    
    print(f"    [policy_agent] Querying vector store: {search_query}")
    
    # Retrieve top 3 relevant policy chunks
    policies = retrieve_relevant_policies(search_query, top_k=3)
    
    # We can also extract some simulated policy IDs or sections if needed.
    # For now, we will just return the retrieved policy texts.
    return {
        "retrieved_policies": policies,
        "matched_policy_ids": ["refund_policy.md"], # Since we only ingested this file for now
    }
