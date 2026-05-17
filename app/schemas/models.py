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


class RiskAnalysis(BaseModel):
    """Structured risk assessment produced by the Risk Agent."""

    risk_score: float = Field(
        description="A risk score between 0.0 (safe) and 1.0 (extremely risky)."
    )
    risk_reason: str = Field(
        description="Detailed explanation of why this risk score was assigned."
    )
    escalation_required: bool = Field(
        description="Whether a human reviewer MUST approve this request based on policy or risk."
    )


class FinalDecision(BaseModel):
    """Final governance decision produced by the Decision Agent."""

    decision: str = Field(
        description="The final verdict: APPROVE, DENY, ESCALATE, or CLARIFY."
    )
    decision_reason: str = Field(
        description="Justification for the decision. If CLARIFY, this should be the polite question asking the user for missing info."
    )
    assigned_reviewer: Optional[str] = Field(
        default=None,
        description="Username or ID of the human reviewer if ESCALATE is chosen."
    )
    escalation_status: Optional[str] = Field(
        default=None,
        description="Status of the escalation: pending_review, review_started, etc."
    )
