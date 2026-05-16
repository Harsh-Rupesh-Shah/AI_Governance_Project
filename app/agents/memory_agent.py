"""
Historical Memory Agent
═══════════════════════
Queries the LangGraph long-term memory store for past decisions,
risk patterns, and incidents related to the current request.

Input from state:  customer_id, action_type
Writes to state:   previous_refunds, suspicious_activity_flags, historical_risk_score
"""

from langgraph.store.base import BaseStore

from app.schemas.models import GovernanceState


def memory_agent(state: GovernanceState, *, store: BaseStore) -> dict:
    """
    LangGraph node: look up historical context from the long-term store.
    The store is injected automatically by LangGraph at runtime.
    """
    customer_id = state.get("customer_id") or "unknown"
    action_type = state.get("action_type") or "unknown"

    # ── Look up past decisions for this customer ─────────────────
    decision_namespace = (customer_id, "decisions")
    past_decisions = store.search(decision_namespace, limit=10)

    previous_refunds = []
    suspicious_flags = []
    risk_scores = []

    for item in past_decisions:
        value = item.value

        # Collect past refund amounts
        if value.get("action_type") == "refund" and value.get("refund_amount"):
            previous_refunds.append(
                f"₹{value['refund_amount']} on {value.get('created_at', 'unknown date')}"
            )

        # Collect any flagged activity
        if value.get("decision") == "DENY" or value.get("decision") == "ESCALATE":
            suspicious_flags.append(
                f"{value.get('decision')}: {value.get('decision_reason', 'no reason')}"
            )

        # Collect past risk scores for averaging
        if value.get("risk_score") is not None:
            risk_scores.append(value["risk_score"])

    # ── Compute historical risk score (average of past scores) ───
    historical_risk_score = None
    if risk_scores:
        historical_risk_score = round(sum(risk_scores) / len(risk_scores), 2)

    return {
        "previous_refunds": previous_refunds,
        "suspicious_activity_flags": suspicious_flags,
        "historical_risk_score": historical_risk_score,
    }
