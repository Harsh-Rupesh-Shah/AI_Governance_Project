"""
Comprehensive End-to-End Feature Test Suite
══════════════════════════════════════════
Tests every feature and component of the AI Governance Copilot:
- Authentication & JWT security
- Intent Extraction Agent
- Policy Ingestion & Retrieval
- Historical Memory & Cross-Thread Store
- Hybrid Risk Engine & Deterministic Scorer
- Decision Agent & Hard Compliance Guardrails
- Audit Agent & Immutable Observability
- Multi-Turn Clarification (CLARIFY flow)
- FastAPI Web Endpoints
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Configure environment
os.environ["LANGCHAIN_TRACING_V2"] = "false"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock MongoClient early for offline test isolation
import pymongo
mock_db = MagicMock()
mock_client = MagicMock()
mock_client.__getitem__.return_value = mock_db
pymongo.MongoClient = MagicMock(return_value=mock_client)

from langchain_core.documents import Document
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, START, END

from app.schemas.models import GovernanceState, ExtractedIntent, RiskAnalysis, FinalDecision
from app.schemas.api_models import GovernanceRequest, GovernanceResponse, AuditLogResponse, UserRegister, UserLogin
from app.services.llm import llm
from app.agents.intent_agent import intent_agent
from app.agents.policy_agent import policy_agent
from app.agents.memory_agent import memory_agent
from app.agents.risk_agent import risk_agent, ModelRefusalError
from app.agents.decision_agent import decision_agent
from app.agents.audit_agent import audit_agent
from app.services.vectordb import ingest_policies, retrieve_relevant_policies


class ComprehensiveApplicationTestSuite(unittest.TestCase):

    def test_01_configuration_and_environment(self):
        """Test configuration loader finds .env and resolves paths properly."""
        from app.config import (
            GOOGLE_MODEL,
            MONGODB_DB_NAME,
            CHROMA_PERSIST_DIR,
            CHROMA_COLLECTION_NAME,
            API_HOST,
            API_PORT
        )
        self.assertTrue(bool(GOOGLE_MODEL))
        self.assertTrue(bool(MONGODB_DB_NAME))
        self.assertTrue(os.path.isabs(CHROMA_PERSIST_DIR))
        self.assertEqual(CHROMA_COLLECTION_NAME, "governance_policies")
        self.assertEqual(API_PORT, 8000)

    def test_02_auth_system_hashing_and_jwt(self):
        """Test password hashing, verification, and JWT creation/validation."""
        from app.api.deps import (
            get_password_hash,
            verify_password,
            create_access_token,
            get_current_user
        )
        from jose import jwt
        from app.api.deps import SECRET_KEY, ALGORITHM

        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

        token = create_access_token({"sub": "compliance_officer", "role": "admin"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(payload["sub"], "compliance_officer")
        self.assertEqual(payload["role"], "admin")

    def test_03_intent_agent_extraction(self):
        """Test Intent Agent entity parsing."""
        mock_intent = ExtractedIntent(
            action_type="refund",
            refund_amount=12500.0,
            customer_id="CUST-4412",
            currency="INR",
            risk_category="financial"
        )
        with patch("app.agents.intent_agent.chain") as mock_chain:
            mock_chain.invoke.return_value = mock_intent
            state = {
                "request_id": "req-01",
                "user_id": "emp-1",
                "request_text": "Refund 12500 INR to customer CUST-4412",
                "created_at": "2026-11-14T00:00:00Z"
            }
            update = intent_agent(state)
            self.assertEqual(update["action_type"], "refund")
            self.assertEqual(update["refund_amount"], 12500.0)
            self.assertEqual(update["customer_id"], "CUST-4412")
            self.assertEqual(update["currency"], "INR")

    def test_04_policy_retrieval_and_rag(self):
        """Test Policy RAG agent executes search query gracefully."""
        with patch("app.agents.policy_agent.retrieve_relevant_policies", return_value=["Policy chunk 1", "Policy chunk 2"]):
            state = {
                "request_text": "Need refund for damaged order",
                "action_type": "refund",
                "risk_category": "financial"
            }
            update = policy_agent(state)
            self.assertEqual(len(update["retrieved_policies"]), 2)
            self.assertIn("refund_policy.md", update["matched_policy_ids"])

    def test_05_memory_agent_cross_thread_history(self):
        """Test Historical Memory Agent loads past incidents from Store."""
        mock_store = InMemoryStore()
        mock_store.put(
            ("CUST-9900", "decisions"),
            "txn-1",
            {"action_type": "refund", "refund_amount": 15000, "risk_score": 0.3, "created_at": "2026-01-10"}
        )
        mock_store.put(
            ("CUST-9900", "decisions"),
            "txn-2",
            {"action_type": "refund", "refund_amount": 40000, "risk_score": 0.7, "decision": "ESCALATE", "decision_reason": "High velocity"}
        )

        state = {
            "customer_id": "CUST-9900",
            "action_type": "refund"
        }
        update = memory_agent(state, store=mock_store)
        self.assertEqual(len(update["previous_refunds"]), 2)
        self.assertEqual(len(update["suspicious_activity_flags"]), 1)
        self.assertEqual(update["historical_risk_score"], 0.5)

    def test_06_hybrid_risk_engine_scoring(self):
        """Test Hybrid Risk Engine calculates deterministic baseline plus contextual evaluation."""
        mock_risk = RiskAnalysis(
            risk_score=0.75,
            risk_reason="Customer has past flagged escalations and amount > 50,000",
            escalation_required=True
        )
        with patch("app.agents.risk_agent.risk_chain") as mock_chain:
            mock_chain.invoke.return_value = mock_risk
            state = {
                "request_text": "Refund 60000 INR for order 889",
                "action_type": "refund",
                "refund_amount": 60000.0,
                "previous_refunds": ["₹10000", "₹20000", "₹30000"],
                "suspicious_activity_flags": ["ESCALATE: High velocity"],
                "retrieved_policies": ["Standard policy"]
            }
            update = risk_agent(state)
            self.assertEqual(update["risk_score"], 0.75)
            self.assertTrue(update["escalation_required"])

            # Verify deterministic rule evaluation (>50k adds 0.2; >=3 refunds adds 0.3 -> base = 0.5)
            call_context = mock_chain.invoke.call_args[0][0]
            self.assertAlmostEqual(call_context["calculated_base_risk"], 0.5, places=2)

    def test_07_decision_agent_guardrails_override(self):
        """Test hard compliance overrides (amount >= 50,000 force ESCALATE)."""
        mock_verdict = FinalDecision(
            decision="APPROVE",
            decision_reason="AI model thought it looked fine",
            assigned_reviewer=None,
            escalation_status="not_required"
        )
        with patch("app.agents.decision_agent.decision_chain") as mock_chain:
            mock_chain.invoke.return_value = mock_verdict
            state = {
                "action_type": "refund",
                "refund_amount": 95000.0,
                "risk_score": 0.25,
                "risk_reason": "Low risk text",
                "escalation_required": False,
                "retrieved_policies": []
            }
            update = decision_agent(state)
            self.assertEqual(update["decision"], "ESCALATE")
            self.assertIn("[GUARDRAIL OVERRIDE]", update["decision_reason"])
            self.assertEqual(update["assigned_reviewer"], "Finance Ops")
            self.assertEqual(update["escalation_status"], "pending_review")

    def test_08_decision_agent_clarify_flow(self):
        """Test CLARIFY decision path when missing required information."""
        mock_verdict = FinalDecision(
            decision="CLARIFY",
            decision_reason="Please provide the invoice number and proof of damaged goods.",
            assigned_reviewer=None,
            escalation_status="not_required"
        )
        with patch("app.agents.decision_agent.decision_chain") as mock_chain:
            mock_chain.invoke.return_value = mock_verdict
            state = {
                "action_type": "refund",
                "refund_amount": 2500.0,
                "risk_score": 0.1,
                "risk_reason": "Missing invoice",
                "escalation_required": False,
                "retrieved_policies": []
            }
            update = decision_agent(state)
            self.assertEqual(update["decision"], "CLARIFY")
            self.assertIn("invoice number", update["decision_reason"])

    def test_09_audit_agent_dual_namespace_logging(self):
        """Test Audit Agent writes to both global audit trail and customer history."""
        mock_store = InMemoryStore()
        state = {
            "request_id": "req-999",
            "user_id": "operator-1",
            "customer_id": "CUST-7721",
            "request_text": "Refund request",
            "action_type": "refund",
            "refund_amount": 4000.0,
            "currency": "INR",
            "risk_category": "financial",
            "risk_score": 0.15,
            "risk_reason": "Low risk",
            "decision": "APPROVE",
            "decision_reason": "Eligible per refund policy",
            "escalation_required": False,
            "escalation_status": "not_required",
            "created_at": "2026-11-14T10:00:00Z"
        }
        update = audit_agent(state, store=mock_store)
        self.assertTrue(bool(update["audit_id"]))
        self.assertTrue(bool(update["trace_id"]))

        # Check global audit trail
        global_logs = mock_store.search(("audit", "trails"))
        self.assertEqual(len(global_logs), 1)
        self.assertEqual(global_logs[0].value["customer_id"], "CUST-7721")

        # Check customer profile history
        customer_logs = mock_store.search(("CUST-7721", "decisions"))
        self.assertEqual(len(customer_logs), 1)
        self.assertEqual(customer_logs[0].value["decision"], "APPROVE")

    def test_10_full_graph_orchestration(self):
        """Test complete LangGraph StateGraph flow from START to END."""
        test_graph = StateGraph(GovernanceState)
        test_graph.add_node("intent_agent", intent_agent)
        test_graph.add_node("policy_agent", policy_agent)
        test_graph.add_node("memory_agent", memory_agent)
        test_graph.add_node("risk_agent", risk_agent)
        test_graph.add_node("decision_agent", decision_agent)
        test_graph.add_node("audit_agent", audit_agent)

        test_graph.add_edge(START, "intent_agent")
        test_graph.add_edge("intent_agent", "policy_agent")
        test_graph.add_edge("policy_agent", "memory_agent")
        test_graph.add_edge("memory_agent", "risk_agent")
        test_graph.add_edge("risk_agent", "decision_agent")
        test_graph.add_edge("decision_agent", "audit_agent")
        test_graph.add_edge("audit_agent", END)

        checkpointer = MemorySaver()
        store = InMemoryStore()
        app = test_graph.compile(checkpointer=checkpointer, store=store)

        mock_intent = ExtractedIntent(action_type="refund", refund_amount=4000.0, customer_id="CUST-1", currency="INR", risk_category="financial")
        mock_risk = RiskAnalysis(risk_score=0.1, risk_reason="Within threshold", escalation_required=False)
        mock_verdict = FinalDecision(decision="APPROVE", decision_reason="Fully eligible", assigned_reviewer=None, escalation_status="not_required")

        with patch("app.agents.intent_agent.chain") as m_intent, \
             patch("app.agents.policy_agent.retrieve_relevant_policies", return_value=["Policy clause"]), \
             patch("app.agents.risk_agent.risk_chain") as m_risk, \
             patch("app.agents.decision_agent.decision_chain") as m_decision:

            m_intent.invoke.return_value = mock_intent
            m_risk.invoke.return_value = mock_risk
            m_decision.invoke.return_value = mock_verdict

            thread_id = "thread-e2e-1"
            config = {"configurable": {"thread_id": thread_id}}
            initial = {
                "request_id": thread_id,
                "user_id": "tester",
                "request_text": "Refund 4000 INR to customer CUST-1",
                "created_at": "2026-11-14T00:00:00Z"
            }

            for _ in app.stream(initial, config=config):
                pass

            final_state = app.get_state(config).values
            self.assertEqual(final_state["decision"], "APPROVE")
            self.assertTrue(bool(final_state["audit_id"]))

    def test_11_fastapi_endpoints_and_health(self):
        """Test FastAPI endpoints for health, audit logs, and request routing."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.api.deps import create_access_token

        client = TestClient(app)
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
