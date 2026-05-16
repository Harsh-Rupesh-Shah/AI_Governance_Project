from typing import TypedDict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class GovernanceState(TypedDict):
    """
    Central shared workflow state
    propagated across all LangGraph agents.
    """

    # Original Request
    request_id: str
    user_id: str
    request_text: str
    created_at: str

    # Intent Extraction
    action_type: Optional[str]
    refund_amount: Optional[float]
    customer_id: Optional[str]
    currency: Optional[str]
    risk_category: Optional[str]

    # Policy Retrieval (RAG)
    retrieved_policies: List[str]
    matched_policy_ids: List[str]

    # Historical Memory
    previous_refunds: List[str]
    suspicious_activity_flags: List[str]
    historical_risk_score: Optional[float]

    # Risk Analysis
    risk_score: Optional[float]
    risk_reason: Optional[str]
    escalation_required: Optional[bool]

    # Final Governance Decision
    decision: Optional[str]
    decision_reason: Optional[str]

    # Audit & Observability
    audit_id: Optional[str]
    trace_id: Optional[str]

    # Human Review
    assigned_reviewer: Optional[str]
    escalation_status: Optional[str]


# ── Structured Output Schemas (for LLM extraction) ──────────────

class ExtractedIntent(BaseModel):
    """Structured intent extracted from a natural language governance request."""

    action_type: str = Field(
        description="Type of action requested: refund, access_request, deployment, data_deletion, etc."
    )
    refund_amount: Optional[float] = Field(
        default=None,
        description="Monetary amount involved, if applicable."
    )
    customer_id: Optional[str] = Field(
        default=None,
        description="Customer identifier, if mentioned in the request."
    )
    currency: Optional[str] = Field(
        default=None,
        description="Currency code (INR, USD, EUR, etc.), if applicable."
    )
    risk_category: str = Field(
        description="Risk category: financial, security, operational, compliance."
    )
