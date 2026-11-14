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


# ── Build the graph ──────────────────────────────────────────────

workflow = StateGraph(GovernanceState)

# Register nodes
workflow.add_node("intent_agent", intent_agent)
workflow.add_node("policy_agent", policy_agent)
workflow.add_node("memory_agent", memory_agent)
workflow.add_node("risk_agent", risk_agent)
workflow.add_node("decision_agent", decision_agent)
workflow.add_node("audit_agent", audit_agent)

# Linear pipeline: START → intent → policy → memory → risk → decision → audit → END
workflow.add_edge(START, "intent_agent")
workflow.add_edge("intent_agent", "policy_agent")
workflow.add_edge("policy_agent", "memory_agent")
workflow.add_edge("memory_agent", "risk_agent")
workflow.add_edge("risk_agent", "decision_agent")
workflow.add_edge("decision_agent", "audit_agent")
workflow.add_edge("audit_agent", END)

# ── Compile with persistence ─────────────────────────────────────
# checkpointer: auto-snapshots GovernanceState after every node (short-term)
# store: cross-thread memory for past decisions, patterns, audits (long-term)
app = workflow.compile(
    checkpointer=checkpointer,
    store=store,
)
