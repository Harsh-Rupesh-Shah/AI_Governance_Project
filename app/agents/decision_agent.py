"""
Decision Agent
══════════════
Final governance verdict using hybrid model:
AI reasoning + deterministic policy enforcement.

Input from state:  risk_score, risk_reason, escalation_required, retrieved_policies
Writes to state:   decision, decision_reason, assigned_reviewer, escalation_status
"""

import logging
from app.schemas.models import GovernanceState, FinalDecision
from app.services.llm import llm

logger = logging.getLogger(__name__)

def decision_agent(state: GovernanceState) -> dict:
    """
    LangGraph node: produce APPROVE / DENY / ESCALATE verdict.
    Separates LLM reasoning from strict deterministic enforcement.
    """
    
    # ── 1. LLM Reasoning (The "Suggestion") ───────────────────────
    context = {
        "intent": {
            "action": state["action_type"],
            "amount": state["refund_amount"]
        },
        "risk": {
            "score": state["risk_score"],
            "reason": state["risk_reason"],
            "escalation_flagged": state["escalation_required"]
        },
        "policies": state["retrieved_policies"]
    }

    prompt = f"""
    You are the Chief Governance Officer. Your goal is to suggest a final decision.
    
    ### CONTEXT:
    {context}

    ### RULES:
    1. If risk['reason'] specifically mentions that mandatory information or documents (like Reason Code, justification) are missing from the user, the decision MUST be 'CLARIFY'. Set 'decision_reason' to a polite question asking the user to provide exactly what is missing.
    2. If risk['escalation_flagged'] is True and it is NOT just missing information, the decision MUST be 'ESCALATE'.
    3. If risk_score > 0.7, the decision should likely be 'DENY' or 'ESCALATE'.
    4. If risk_score < 0.3 and no policy violations, 'APPROVE'.
    
    ### RESPONSE FORMAT:
    You must return a structured final decision.
    """

    structured_llm = llm.with_structured_output(FinalDecision)
    verdict = structured_llm.invoke(prompt)

    # ── 2. Governance Enforcement (The "Guardrail") ────────────────
    final_decision = verdict.decision
    final_reason = verdict.decision_reason

    amount = state.get("refund_amount") or 0.0

    # Guardrail A: Risk Agent Flag
    if state.get("escalation_required") and final_decision not in ["ESCALATE", "CLARIFY"]:
        final_decision = "ESCALATE"
        final_reason = f"[GUARDRAIL OVERRIDE] Risk Agent flagged for mandatory escalation. Original AI reason: {verdict.decision_reason}"

    # Guardrail B: Hard Amount Threshold 
    # (Using 50,000 as an example operational threshold; in production this would be loaded from a DB/Config)
    HARD_ESCALATION_THRESHOLD = 50000.0
    if amount >= HARD_ESCALATION_THRESHOLD and final_decision == "APPROVE":
        final_decision = "ESCALATE"
        final_reason = f"[GUARDRAIL OVERRIDE] Amount ({amount}) exceeds operational hard limit of {HARD_ESCALATION_THRESHOLD}. Original AI reason: {verdict.decision_reason}"

    # Guardrail C: High Risk Score cutoff (Step 14 Human-in-the-Loop)
    if state.get("risk_score", 0.0) >= 0.8 and final_decision == "APPROVE":
        final_decision = "ESCALATE"
        verdict.assigned_reviewer = "Finance Ops"
        final_reason = f"[GUARDRAIL OVERRIDE] Risk score is critically high ({state.get('risk_score')}). Forcing Human-in-the-loop review. Original AI reason: {verdict.decision_reason}"

    logger.info(f"Suggested: {verdict.decision} -> Enforced: {final_decision}")

    return {
        "decision": final_decision,
        "decision_reason": final_reason,
        "assigned_reviewer": verdict.assigned_reviewer or ("Finance Ops" if final_decision == "ESCALATE" else None),
        "escalation_status": "pending_review" if final_decision == "ESCALATE" else "not_required"
    }

