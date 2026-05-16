"""
End-to-End Sample Request Runner
══════════════════════════════════
Runs one governance request through the full LangGraph workflow.

What this tests:
- intent_agent:   Real LLM extraction (Gemini)
- policy_agent:   Placeholder (returns empty)
- memory_agent:   Queries MongoDBStore for past decisions
- risk_agent:     Placeholder (returns null)
- decision_agent: Placeholder (defaults to ESCALATE)
- audit_agent:    Writes full audit record to MongoDBStore

Run from project root:
    python run_sample.py
"""

import uuid
import json
import sys
import os
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.workflow import app


# ── Sample Request ────────────────────────────────────────────────

REQUEST_TEXT = "Please refund 75000 INR to customer CUST-8872 for a failed payment on order ORD-9912."

initial_state = {
    # Core request fields
    "request_id":  str(uuid.uuid4()),
    "user_id":     "agent-user-001",
    "request_text": REQUEST_TEXT,
    "created_at":  datetime.now(timezone.utc).isoformat(),

    # All agent-written fields start as None / empty
    "action_type":              None,
    "refund_amount":            None,
    "customer_id":              None,
    "currency":                 None,
    "risk_category":            None,
    "retrieved_policies":       [],
    "matched_policy_ids":       [],
    "previous_refunds":         [],
    "suspicious_activity_flags": [],
    "historical_risk_score":    None,
    "risk_score":               None,
    "risk_reason":              None,
    "escalation_required":      None,
    "decision":                 None,
    "decision_reason":          None,
    "audit_id":                 None,
    "trace_id":                 None,
    "assigned_reviewer":        None,
    "escalation_status":        None,
}

# Each run gets a unique thread_id — this is what the checkpointer uses
# to identify and store the state snapshots in MongoDB
config = {
    "configurable": {
        "thread_id": initial_state["request_id"]
    }
}


# ── Run ──────────────────────────────────────────────────────────

def run():
    print("\n" + "═" * 60)
    print("  AI Governance Copilot — End-to-End Sample Run")
    print("═" * 60)
    print(f"\n📥 REQUEST:\n   {REQUEST_TEXT}")
    print(f"\n🔑 Thread ID: {initial_state['request_id']}")
    print("\n⏳ Running workflow...\n")

    # Stream events so we can see each agent as it executes
    for step_num, event in enumerate(
        app.stream(initial_state, config=config, stream_mode="updates"), start=1
    ):
        for agent_name, state_update in event.items():
            print(f"  [{step_num}] ✅ {agent_name}")
            for key, value in state_update.items():
                if value is not None and value != [] and value != "":
                    print(f"        {key}: {value}")

    print("\n" + "─" * 60)

    # Fetch final state from the checkpointer
    final_snapshot = app.get_state(config)
    final_state = final_snapshot.values

    print("\n📊 FINAL STATE SUMMARY")
    print("─" * 60)

    sections = {
        "Intent Extraction": ["action_type", "refund_amount", "customer_id", "currency", "risk_category"],
        "Policy Retrieval":  ["retrieved_policies", "matched_policy_ids"],
        "Historical Memory": ["previous_refunds", "suspicious_activity_flags", "historical_risk_score"],
        "Risk Analysis":     ["risk_score", "risk_reason", "escalation_required"],
        "Decision":          ["decision", "decision_reason", "assigned_reviewer", "escalation_status"],
        "Audit":             ["audit_id", "trace_id"],
    }

    for section, fields in sections.items():
        print(f"\n  {section}:")
        for field in fields:
            val = final_state.get(field)
            if val is not None and val != [] and val != "":
                print(f"    {field}: {val}")
            else:
                print(f"    {field}: —")

    print("\n" + "═" * 60)
    print(f"\n✅ Done. Audit ID: {final_state.get('audit_id')}")
    print(f"   This run is checkpointed in MongoDB under thread: {initial_state['request_id']}")
    print(f"   Audit record written to MongoDBStore under customer: {final_state.get('customer_id', 'unknown')}\n")


if __name__ == "__main__":
    run()
