import uuid
import sys
import os
import io
import logging
from datetime import datetime, timezone

# Reconfigure stdout to use UTF-8 to prevent charmap errors on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.workflow import app

# ── Configure Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("InteractiveCLI")

def run():
    print("\n" + "=" * 80)
    print("🤖 AI Governance Copilot - Interactive Terminal")
    print("=" * 80)
    print("Type your request below. Type 'exit' or 'quit' to stop.")

    # Conversation state
    current_request_text = ""
    clarifying = False

    while True:
        print("\n" + "-" * 80)
        
        if clarifying:
            prompt_text = "🗣️ PLEASE CLARIFY: "
        else:
            prompt_text = "👤 YOU: "
            
        user_input = input(f"\n{prompt_text}").strip()

        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        if clarifying:
            current_request_text += f"\n\nUser Clarification: {user_input}"
            clarifying = False
        else:
            current_request_text = user_input

        request_id = str(uuid.uuid4())
        
        initial_state = {
            "request_id":  request_id,
            "user_id":     "terminal-user",
            "request_text": current_request_text,
            "created_at":  datetime.now(timezone.utc).isoformat(),
        }

        config = {"configurable": {"thread_id": request_id}}

        logger.info(f"Starting workflow for request ID: {request_id}")
        
        # Stream events
        try:
            for event in app.stream(initial_state, config=config, stream_mode="updates"):
                for agent_name, state_update in event.items():
                    logger.info(f"Node Executed: [{agent_name}]")
        except Exception as e:
            logger.error(f"Error during workflow execution: {e}")
            continue

        # Fetch final state
        final_snapshot = app.get_state(config)
        final_state = final_snapshot.values
        
        decision = final_state.get('decision', 'N/A')
        reason = final_state.get('decision_reason', 'N/A')
        
        if decision == "CLARIFY":
            print("\n" + "=" * 80)
            print("🛑 AI NEEDS MORE INFORMATION")
            print("=" * 80)
            print(f"💡 {reason}")
            clarifying = True
            continue

        print("\n" + "=" * 80)
        print("🧠 AI DECISION SUMMARY")
        print("=" * 80)
        
        # Extracted Intent
        action = final_state.get('action_type', 'N/A')
        amount = final_state.get('refund_amount', 'N/A')
        cust_id = final_state.get('customer_id', 'N/A')
        print(f"📌 Intent Extract : {action.upper()} | Amount: {amount} | Customer: {cust_id}")
        
        # Memory & Policy
        policies = len(final_state.get('retrieved_policies', []))
        history_len = len(final_state.get('previous_refunds', []))
        print(f"📚 Context loaded: {policies} policies retrieved, {history_len} past incidents found.")
        
        # Risk
        risk_score = final_state.get('risk_score', 'N/A')
        risk_reason = final_state.get('risk_reason', 'N/A')
        print(f"⚠️ Risk Score     : {risk_score}")
        print(f"📝 Risk Reason    : {risk_reason}")

        reviewer = final_state.get('assigned_reviewer', 'None')
        
        print("\n" + "-" * 80)
        if decision == "APPROVE":
            print(f"✅ FINAL VERDICT: APPROVE")
        elif decision == "DENY":
            print(f"❌ FINAL VERDICT: DENY")
        else:
            print(f"🚨 FINAL VERDICT: ESCALATE (Assigned to: {reviewer})")
            
        print(f"💡 Explanation  : {reason}")
        print("-" * 80)
        
        audit_id = final_state.get('audit_id')
        logger.info(f"Workflow complete. Audit ID: {audit_id}")


if __name__ == "__main__":
    run()
