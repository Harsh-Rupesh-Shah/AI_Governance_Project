import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuditLogs } from '../api';

export default function Audit() {
  const navigate = useNavigate();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await getAuditLogs();
        setLogs(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const renderBadge = (status: string) => {
    if (status === 'APPROVE') return <span className="badge success">APPROVE</span>;
    if (status === 'DENY' || status === 'ESCALATE') return <span className="badge danger">{status}</span>;
    if (status === 'CLARIFY') return <span className="badge warning">CLARIFY</span>;
    return <span className="badge">{status}</span>;
  };

  return (
    <div className="app-container">
      <header className="navbar">
        <h1>Finance Ops Control Center</h1>
        <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
          <span className="badge" style={{cursor: 'pointer'}} onClick={() => navigate('/workspace')}>Back to Workspace</span>
        </div>
      </header>

      <main className="workspace" style={{maxWidth: '1600px'}}>
        <section className="panel" style={{ width: '100%' }}>
          <h3>Audit Ledger</h3>
          
          {loading ? (
            <p>Loading historical data...</p>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Audit ID</th>
                    <th>Timestamp</th>
                    <th>User / Subject</th>
                    <th>Intent</th>
                    <th>Risk Score</th>
                    <th>Final Verdict</th>
                    <th>Assigned To</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.length === 0 ? (
                    <tr><td colSpan={7} style={{textAlign: 'center'}}>No audit logs found.</td></tr>
                  ) : logs.map((log) => (
                    <tr key={log.audit_id}>
                      <td style={{fontFamily: 'monospace', fontSize: '0.75rem'}}>{log.audit_id.slice(0,8)}...</td>
                      <td>{new Date(log.created_at).toLocaleString()}</td>
                      <td>{log.customer_id || 'Unknown'}</td>
                      <td>{log.action_type?.toUpperCase() || 'N/A'}</td>
                      <td>
                        <strong>{log.risk_score !== null ? log.risk_score.toFixed(2) : '-'}</strong>
                      </td>
                      <td>{renderBadge(log.decision)}</td>
                      <td>{log.assigned_reviewer || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
