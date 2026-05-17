"""
Risk Analysis Agent
═══════════════════
Combines deterministic rules, retrieved policies, historical memory,
and LLM reasoning to produce an explainable risk score.

Input from state:  action_type, refund_amount, retrieved_policies, previous_refunds, historical_risk_score
Writes to state:   risk_score, risk_reason, escalation_required
"""

import logging
from app.schemas.models import GovernanceState, RiskAnalysis
from app.services.llm import llm

logger = logging.getLogger(__name__)

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
        "request": state["request_text"],
        "action": state["action_type"],
        "amount": amount,
        "policies": state["retrieved_policies"],
        "history_flags": state["suspicious_activity_flags"],
        "calculated_base_risk": base_risk,
        "deterministic_reasons": deterministic_reasons
    }

    prompt = f"""
    You are an AI Risk Auditor for an enterprise governance system.
    Our deterministic rules engine has calculated a base risk score.
    Your job is to provide contextual reasoning and output the final structured analysis.

    ### CONTEXT:
    {context}

    ### INSTRUCTIONS:
    - Review the user's raw request against the policies.
    - Factor in the 'calculated_base_risk' ({base_risk}). You may adjust it slightly (+/- 0.1) if the context of the text strongly suggests fraud or a harmless mistake, but generally stick close to the base risk.
    - Check the policies to see if this request violates a 'BLOCK' or 'ESCALATE' rule. If so, set escalation_required to True.
    - Provide a detailed 'risk_reason' explaining the final score.

    ### RESPONSE FORMAT:
    You must return a structured risk analysis.
    """

    # Use structured output
    structured_llm = llm.with_structured_output(RiskAnalysis)
    analysis = structured_llm.invoke(prompt)

    logger.info(f"Hybrid Risk Score: {analysis.risk_score} (Base was {base_risk})")
    logger.info(f"Reason: {analysis.risk_reason[:100]}...")

    return {
        "risk_score": analysis.risk_score,
        "risk_reason": analysis.risk_reason,
        "escalation_required": analysis.escalation_required
    }

