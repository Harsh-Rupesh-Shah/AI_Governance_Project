import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.intent_agent import intent_agent
from app.schemas.models import GovernanceState

def test_run():
    # 1. Mock the initial state (what the API would send)
    mock_state: GovernanceState = {
        "request_id": "test-123",
        "user_id": "user-99",
        "request_text": "Please refund 5000 INR to customer CUST-8872 immediately for the failed transaction.",
        "created_at": "2024-01-01T00:00:00",
        "action_type": None,
        "refund_amount": None,
        "customer_id": None,
        "currency": None,
        "risk_category": None,
        "retrieved_policies": [],
        "matched_policy_ids": [],
        "previous_refunds": [],
        "suspicious_activity_flags": [],
        "historical_risk_score": None,
        "risk_score": None,
        "risk_reason": None,
        "escalation_required": None,
        "decision": None,
        "decision_reason": None,
        "audit_id": None,
        "trace_id": None,
        "assigned_reviewer": None,
        "escalation_status": None
    }

    print("\n--- Sending Request to Intent Agent ---")
    print(f"Input: {mock_state['request_text']}")
    
    # 2. Run the agent
    try:
        updated_fields = intent_agent(mock_state)
        
        # 3. Print the results
        print("\n--- Extracted Structured Intent ---")
        print(json.dumps(updated_fields, indent=4))
    except Exception as e:
        print(f"\n[ERROR] Ensure your GOOGLE_API_KEY is set in .env")
        print(f"Details: {e}")

if __name__ == "__main__":
    test_run()
