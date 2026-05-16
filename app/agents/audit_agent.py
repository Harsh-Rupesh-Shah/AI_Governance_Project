"""
Audit & Observability Agent
═══════════════════════════
Persists the full execution trace to the LangGraph long-term
memory store for governance transparency and compliance.

Input from state:  (reads entire state)
Writes to state:   audit_id, trace_id
"""

import uuid
from datetime import datetime, timezone

from langgraph.store.base import BaseStore

from app.schemas.models import GovernanceState


def audit_agent(state: GovernanceState, *, store: BaseStore) -> dict:
    """
    LangGraph node: persist the full audit trail to the long-term store.
    The store is injected automatically by LangGraph at runtime.
    """
    audit_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    customer_id = state.get("customer_id") or "unknown"

    # ── Build the audit record ───────────────────────────────────
    audit_record = {
        "audit_id": audit_id,
        "trace_id": trace_id,
        "request_id": state.get("request_id"),
        "user_id": state.get("user_id"),
        "customer_id": customer_id,
        "request_text": state.get("request_text"),
        "action_type": state.get("action_type"),
        "refund_amount": state.get("refund_amount"),
        "currency": state.get("currency"),
        "risk_category": state.get("risk_category"),
        "risk_score": state.get("risk_score"),
        "risk_reason": state.get("risk_reason"),
        "decision": state.get("decision"),
        "decision_reason": state.get("decision_reason"),
        "escalation_required": state.get("escalation_required"),
        "escalation_status": state.get("escalation_status"),
        "matched_policy_ids": state.get("matched_policy_ids", []),
        "created_at": state.get("created_at"),
        "audited_at": now,
    }

    # ── Persist to long-term store ───────────────────────────────

    # 1. Save to audit namespace (global audit trail)
    store.put(("audit", "trails"), audit_id, audit_record)

    # 2. Save to customer's decision history (for memory_agent lookups)
    store.put(
        (customer_id, "decisions"),
        state.get("request_id", audit_id),
        audit_record,
    )

    return {
        "audit_id": audit_id,
        "trace_id": trace_id,
    }
