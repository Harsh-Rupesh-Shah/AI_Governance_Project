"""
Risk Analysis Agent
═══════════════════
Combines deterministic rules, retrieved policies, historical memory,
and LLM reasoning to produce an explainable risk score.

Input from state:  action_type, refund_amount, retrieved_policies, previous_refunds, historical_risk_score
Writes to state:   risk_score, risk_reason, escalation_required
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
try:
    from langchain_core.exceptions import ModelRefusalError
except ImportError:
    class ModelRefusalError(Exception):
        def __init__(self, message="Model refusal"):
            super().__init__(message)
            self.raw_message = message

from app.schemas.models import GovernanceState, RiskAnalysis
from app.services.llm import llm

logger = logging.getLogger(__name__)

# ── Prompts & Structured LLM Chain (Module Level) ────────────────
SYSTEM_PROMPT = """You are an AI Risk Auditor for an enterprise governance system.
Our deterministic rules engine has calculated a base risk score.
Your job is to provide contextual reasoning and output the final structured analysis.

Instructions:
- Review the user's raw request against the policies.
- Factor in the 'calculated_base_risk'. You may adjust it slightly (+/- 0.1) if the context of the text strongly suggests fraud or a harmless mistake, but generally stick close to the base risk.
- Check the policies to see if this request violates a 'BLOCK' or 'ESCALATE' rule. If so, set escalation_required to True.
- Provide a detailed 'risk_reason' explaining the final score.
"""

HUMAN_PROMPT = """Context:
- Request: {request}
- Action: {action}
- Amount: {amount}
- Policies: {policies}
- History Flags: {history_flags}
- Calculated Base Risk: {calculated_base_risk}
- Deterministic Reasons: {deterministic_reasons}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_PROMPT),
])

structured_llm = llm.with_structured_output(RiskAnalysis)
risk_chain = prompt | structured_llm

def risk_agent(state: GovernanceState) -> dict:
    """
    LangGraph node: assess risk level.
    Uses a HYBRID Risk Engine (Deterministic Rules + LLM Contextual Reasoning).
    """
    
    # ── 1. Deterministic Risk Scoring ────────────────────────────
    base_risk = 0.0
    deterministic_reasons = []

    amount = state.get("refund_amount") or 0.0
    previous_refunds = state.get("previous_refunds", [])

    # Rule: High value amounts
    if amount > 100000:
        base_risk += 0.4
        deterministic_reasons.append("Amount exceeds 100,000.")
    elif amount > 50000:
        base_risk += 0.2
        deterministic_reasons.append("Amount exceeds 50,000.")

    # Rule: Historical velocity/abuse
    if len(previous_refunds) >= 3:
        base_risk += 0.3
        deterministic_reasons.append("Customer has 3 or more previous refunds.")
    elif len(previous_refunds) >= 1:
        base_risk += 0.1
        deterministic_reasons.append("Customer has prior refund history.")

    # Cap base risk at 1.0
    base_risk = min(base_risk, 1.0)

    # ── 2. LLM Contextual Reasoning ──────────────────────────────
    context = {
        "request": state.get("request_text", ""),
        "action": state.get("action_type") or "unknown",
        "amount": amount,
        "policies": state.get("retrieved_policies", []),
        "history_flags": state.get("suspicious_activity_flags", []),
        "calculated_base_risk": base_risk,
        "deterministic_reasons": deterministic_reasons
    }

    try:
        analysis: RiskAnalysis = risk_chain.invoke(context)
        risk_score = analysis.risk_score
        risk_reason = analysis.risk_reason
        escalation_required = analysis.escalation_required
    except ModelRefusalError as e:
        logger.warning(f"Model refused risk analysis: {e.raw_message}")
        risk_score = 1.0
        risk_reason = f"[REFUSAL OVERRIDE] Safety or policy refusal by model: {e.raw_message}"
        escalation_required = True

    logger.info(f"Hybrid Risk Score: {risk_score} (Base was {base_risk})")
    logger.info(f"Reason: {risk_reason[:100]}...")

    return {
        "risk_score": risk_score,
        "risk_reason": risk_reason,
        "escalation_required": escalation_required
    }

