"""
LangGraph Governance Workflow
═════════════════════════════
Orchestrates the full decision governance pipeline as a StateGraph.

Flow:
  START → intent_agent → policy_agent → memory_agent → risk_agent → decision_agent
         ↓                                                            ↓
         (linear)                                                  (conditional)
                                                               ┌──────┼──────┐
                                                            APPROVE  DENY  ESCALATE
                                                               └──────┼──────┘
                                                                      ↓
                                                                 audit_agent → END
"""

from langgraph.graph import StateGraph, START, END

from app.schemas.models import GovernanceState
from app.services.persistence import checkpointer, store

# ── Import agent node functions ──────────────────────────────────
from app.agents.intent_agent import intent_agent
from app.agents.policy_agent import policy_agent
from app.agents.memory_agent import memory_agent
from app.agents.risk_agent import risk_agent
from app.agents.decision_agent import decision_agent
from app.agents.audit_agent import audit_agent


# ── Routing function after decision_agent ────────────────────────

def route_after_decision(state: GovernanceState) -> str:
    """
    Conditional edge: inspects the decision field and routes accordingly.
    All paths lead to audit_agent for traceability.
    """
    decision = state.get("decision", "ESCALATE")

    if decision == "APPROVE":
        return "audit_agent"
    elif decision == "DENY":
        return "audit_agent"
    else:
        # ESCALATE (or unknown) → still audit, but escalation_status is set by decision_agent
        return "audit_agent"


# ── Build the graph ──────────────────────────────────────────────

workflow = StateGraph(GovernanceState)

# Register nodes
workflow.add_node("intent_agent", intent_agent)
workflow.add_node("policy_agent", policy_agent)
workflow.add_node("memory_agent", memory_agent)
workflow.add_node("risk_agent", risk_agent)
workflow.add_node("decision_agent", decision_agent)
workflow.add_node("audit_agent", audit_agent)

# Linear edges: START → intent → policy → memory → risk → decision
workflow.add_edge(START, "intent_agent")
workflow.add_edge("intent_agent", "policy_agent")
workflow.add_edge("policy_agent", "memory_agent")
workflow.add_edge("memory_agent", "risk_agent")
workflow.add_edge("risk_agent", "decision_agent")

# Conditional edge after decision: routes based on APPROVE / DENY / ESCALATE
workflow.add_conditional_edges(
    "decision_agent",
    route_after_decision,
    {
        "audit_agent": "audit_agent",
    },
)

# All paths end after audit
workflow.add_edge("audit_agent", END)

# ── Compile with persistence ─────────────────────────────────────
# checkpointer: auto-snapshots GovernanceState after every node (short-term)
# store: cross-thread memory for past decisions, patterns, audits (long-term)
app = workflow.compile(
    checkpointer=checkpointer,
    store=store,
)
