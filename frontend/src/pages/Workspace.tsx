import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitGovernanceRequest } from '../api';

export default function Workspace() {
  const navigate = useNavigate();
  const [requestText, setRequestText] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Response State
  const [decision, setDecision] = useState<string | null>(null);
  const [reason, setReason] = useState<string | null>(null);
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [auditId, setAuditId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setDecision(null);
    try {
      const res = await submitGovernanceRequest(requestText);
      setDecision(res.data.decision);
      setReason(res.data.decision_reason);
      setRiskScore(res.data.risk_score);
      setAuditId(res.data.audit_id);
      if (res.data.decision !== 'CLARIFY') {
        setRequestText(''); // clear on finish
      }
    } catch (err) {
      console.error(err);
      alert("Failed to submit request.");
    } finally {
      setLoading(false);
    }
  };

  const renderBadge = (status: string) => {
    if (status === 'APPROVE') return <span className="badge success">APPROVED</span>;
    if (status === 'DENY' || status === 'ESCALATE') return <span className="badge danger">{status}</span>;
    if (status === 'CLARIFY') return <span className="badge warning">CLARIFY</span>;
    return <span className="badge">{status}</span>;
  };

  return (
    <div className="app-container">
      <header className="navbar">
        <h1>AI Governance Copilot</h1>
        <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
          <span className="badge" style={{cursor: 'pointer'}} onClick={() => navigate('/audit')}>View Audits</span>
          <span className="badge danger" style={{cursor: 'pointer'}} onClick={() => {
            localStorage.removeItem('token');
            navigate('/');
          }}>Logout</span>
        </div>
      </header>

      <main className="workspace">
        {/* Left Pane - User Input */}
        <section className="panel" style={{ flex: 1.2 }}>
          <h3>Submit New Request</h3>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Request Details</label>
              <textarea 
                className="input-field" 
                placeholder="e.g., I need a refund of 5000 INR for order 123 due to damaged goods..."
                value={requestText}
                onChange={(e) => setRequestText(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Analyzing via LangGraph...' : 'Submit for AI Review'}
            </button>
          </form>

          {decision === 'CLARIFY' && (
            <div className="alert warning" style={{ marginTop: '2rem' }}>
              <strong>🛑 AI Needs More Information</strong>
              <p style={{ marginTop: '0.5rem' }}>{reason}</p>
              <p style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#b45309' }}>
                * Type your clarification in the box above and submit again. The LangGraph thread is preserved!
              </p>
            </div>
          )}
        </section>

        {/* Right Pane - AI Transparency View */}
        <section className="panel" style={{ flex: 1, backgroundColor: '#f8fafc' }}>
          <h3>AI Governance X-Ray</h3>
          
          {!decision && !loading && (
            <p style={{color: 'var(--text-secondary)', fontStyle: 'italic'}}>Waiting for request submission...</p>
          )}

          {loading && (
            <div style={{textAlign: 'center', padding: '2rem 0', color: 'var(--primary)'}}>
              <div className="spinner">Evaluating intent, risk, and policy...</div>
            </div>
          )}

          {decision && !loading && (
            <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
              
              <div>
                <label style={{fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase'}}>
                  Final Verdict
                </label>
                <div style={{marginTop: '0.25rem', fontSize: '1.25rem'}}>
                  {renderBadge(decision)}
                </div>
              </div>

              <div>
                <label style={{fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase'}}>
                  Hybrid Risk Score
                </label>
                <div style={{marginTop: '0.25rem', fontSize: '1.5rem', fontWeight: 700}}>
                  {riskScore !== null ? riskScore.toFixed(2) : 'N/A'}
                </div>
              </div>

              <div>
                <label style={{fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase'}}>
                  Decision Reasoning
                </label>
                <p style={{marginTop: '0.25rem', fontSize: '0.875rem', background: '#fff', padding: '0.75rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius)'}}>
                  {reason}
                </p>
              </div>

              {auditId && (
                <div>
                  <label style={{fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase'}}>
                    Audit Trace ID
                  </label>
                  <p style={{marginTop: '0.25rem', fontSize: '0.875rem', fontFamily: 'monospace'}}>
                    {auditId}
                  </p>
                </div>
              )}

            </div>
          )}
        </section>
      </main>
    </div>
  );
}
