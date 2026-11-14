"""
Decision Agent
══════════════
Final governance verdict using hybrid model:
AI reasoning + deterministic policy enforcement.

Input from state:  risk_score, risk_reason, escalation_required, retrieved_policies
Writes to state:   decision, decision_reason, assigned_reviewer, escalation_status
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

from app.schemas.models import GovernanceState, FinalDecision
from app.services.llm import llm

logger = logging.getLogger(__name__)

# ── Prompts & Structured LLM Chain (Module Level) ────────────────
SYSTEM_PROMPT = """You are the Chief Governance Officer. Your goal is to suggest a final decision.

Rules:
1. If risk['reason'] specifically mentions that mandatory information or documents (like Reason Code, justification) are missing from the user, the decision MUST be 'CLARIFY'. Set 'decision_reason' to a polite question asking the user to provide exactly what is missing.
2. If risk['escalation_flagged'] is True and it is NOT just missing information, the decision MUST be 'ESCALATE'.
3. If risk_score > 0.7, the decision should likely be 'DENY' or 'ESCALATE'.
4. If risk_score < 0.3 and no policy violations, 'APPROVE'.
"""

HUMAN_PROMPT = """Context:
Intent:
  - Action: {action}
  - Amount: {amount}
Risk Assessment:
  - Score: {risk_score}
  - Reason: {risk_reason}
  - Escalation Flagged: {escalation_flagged}
Policies Retrieved:
  {policies}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_PROMPT),
])

structured_llm = llm.with_structured_output(FinalDecision)
decision_chain = prompt | structured_llm

def decision_agent(state: GovernanceState) -> dict:
    """
    LangGraph node: produce APPROVE / DENY / ESCALATE verdict.
    Separates LLM reasoning from strict deterministic enforcement.
    """
    
    # ── 1. LLM Reasoning (The "Suggestion") ───────────────────────
    context = {
        "action": state.get("action_type") or "unknown",
        "amount": state.get("refund_amount"),
        "risk_score": state.get("risk_score"),
        "risk_reason": state.get("risk_reason") or "N/A",
        "escalation_flagged": state.get("escalation_required", False),
        "policies": state.get("retrieved_policies", []),
    }

    try:
        verdict: FinalDecision = decision_chain.invoke(context)
        suggested_decision = verdict.decision
        suggested_reason = verdict.decision_reason
        assigned_reviewer = verdict.assigned_reviewer
    except ModelRefusalError as e:
        logger.warning(f"Model refused decision evaluation: {e.raw_message}")
        suggested_decision = "ESCALATE"
        suggested_reason = f"[REFUSAL OVERRIDE] Safety or policy refusal by model: {e.raw_message}"
        assigned_reviewer = "Finance Ops"

    # ── 2. Governance Enforcement (The "Guardrail") ────────────────
    final_decision = suggested_decision
    final_reason = suggested_reason

    amount = state.get("refund_amount") or 0.0

    # Guardrail A: Risk Agent Flag
    if state.get("escalation_required") and final_decision not in ["ESCALATE", "CLARIFY"]:
        final_decision = "ESCALATE"
        final_reason = f"[GUARDRAIL OVERRIDE] Risk Agent flagged for mandatory escalation. Original AI reason: {suggested_reason}"

    # Guardrail B: Hard Amount Threshold 
    HARD_ESCALATION_THRESHOLD = 50000.0
    if amount >= HARD_ESCALATION_THRESHOLD and final_decision == "APPROVE":
        final_decision = "ESCALATE"
        final_reason = f"[GUARDRAIL OVERRIDE] Amount ({amount}) exceeds operational hard limit of {HARD_ESCALATION_THRESHOLD}. Original AI reason: {suggested_reason}"

    # Guardrail C: High Risk Score cutoff
    if (state.get("risk_score") or 0.0) >= 0.8 and final_decision == "APPROVE":
        final_decision = "ESCALATE"
        assigned_reviewer = "Finance Ops"
        final_reason = f"[GUARDRAIL OVERRIDE] Risk score is critically high ({state.get('risk_score')}). Forcing Human-in-the-loop review. Original AI reason: {suggested_reason}"

    logger.info(f"Suggested: {suggested_decision} -> Enforced: {final_decision}")

    return {
        "decision": final_decision,
        "decision_reason": final_reason,
        "assigned_reviewer": assigned_reviewer or ("Finance Ops" if final_decision == "ESCALATE" else None),
        "escalation_status": "pending_review" if final_decision == "ESCALATE" else "not_required"
    }

