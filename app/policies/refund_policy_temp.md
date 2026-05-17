# Corporate Refund and Dispute Resolution Policy
**Effective Date:** January 1, 2026
**Version:** 3.4
**Owner:** Global Finance & Operations
**Scope:** All subsidiaries, partners, and customer-facing support teams.

## 1. Introduction
This document outlines the standard operating procedures, thresholds, and governance mechanisms for processing customer refunds, chargebacks, and financial disputes. All agents (human and AI) must adhere strictly to these guidelines.

## 2. Standard Refund Thresholds (Domestic - INR)
Refunds are categorized by monetary value to ensure proper oversight and risk management.

### 2.1 Tier 1: Auto-Approval (Below ₹10,000)
- **Condition:** Customer is in good standing (account age > 30 days, no prior fraud flags).
- **Process:** Can be processed immediately by Level 1 support or automated agents without human intervention.
- **SLA:** 24 hours.

### 2.2 Tier 2: Standard Review (₹10,000 to ₹50,000)
- **Condition:** Requires verification of the original transaction and service failure context.
- **Process:** Automated agents can prepare the case, but it requires approval from a Level 2 Support Specialist.
- **SLA:** 48 hours.

### 2.3 Tier 3: Manual Approval Required (Above ₹50,000 to ₹1,00,000)
- **Condition:** High-value transaction. Requires proof of return, defect, or SLA breach.
- **Process:** Must be reviewed and manually approved by a Support Manager.
- **SLA:** 3-5 business days.

### 2.4 Tier 4: Finance Escalation (Above ₹1,00,000)
- **Condition:** Exceptional value.
- **Process:** MUST be escalated directly to Finance Operations (`fin-ops@company.internal`).
- **SLA:** 7-10 business days.

## 3. High-Risk and Suspicious Activity
To prevent financial fraud, the following conditions trigger automatic risk flags regardless of the refund amount.

### 3.1 Velocity Checks
- **Condition:** More than 3 refunds requested by the same `customer_id` within a rolling 24-hour period.
- **Action:** Reject immediate processing. Route to the Fraud & Risk team for a "Suspicious Activity Review".

### 3.2 Age of Transaction
- **Condition:** Refund requested for a transaction older than 90 days.
- **Action:** Standard refund is denied. Must be processed as a "Goodwill Credit" requiring Director-level approval.

### 3.3 Payment Method Mismatch
- **Condition:** Customer requests a refund to a different account or payment method than the original transaction.
- **Action:** Strictly prohibited due to Anti-Money Laundering (AML) regulations. Deny request.

## 4. International and Cross-Border Refunds
International transactions carry foreign exchange (FX) and regulatory risks.

### 4.1 Currency Limitations
- **Condition:** Refunds must be processed in the original billing currency (e.g., USD, EUR, GBP).

### 4.2 Compliance Validation
- **Condition:** All international refunds, regardless of amount, require compliance validation to ensure adherence to OFAC and local export/trade regulations.
- **Action:** Route to the Global Trade Compliance team before processing.

## 5. Non-Refundable Items
The following items/services are strictly non-refundable under any circumstances:
- Digital gift cards and prepaid wallet top-ups.
- Software licenses that have been activated and used for more than 48 hours.
- Custom enterprise development hours already logged and approved by the client.

## 6. Audit and Traceability
Every refund decision (Approve, Deny, or Escalate) must be logged in the centralized Governance Memory Store with a unique `audit_id`, `trace_id`, and a clear `decision_reason` referencing the specific section of this policy.
