import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register } from '../api';

export default function Login() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isLogin) {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        const res = await login(params);
        localStorage.setItem('token', res.data.access_token);
      } else {
        const res = await register({ username, password, role: 'employee' });
        localStorage.setItem('token', res.data.access_token);
      }
      navigate('/workspace');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>AI Governance Platform</h2>
        <p>Authorized Personnel Only</p>
        
        {error && <div className="alert danger" style={{marginBottom: '1rem', color: 'var(--danger)'}}>{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input 
              type="text" 
              className="input-field" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Processing...' : (isLogin ? 'Secure Login' : 'Register Account')}
          </button>
        </form>
        
        <p style={{marginTop: '1.5rem', textAlign: 'center', cursor: 'pointer', color: 'var(--primary)'}} onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? "Need an account? Register here." : "Already have an account? Login here."}
        </p>
      </div>
    </div>
  );
}
