import React, { useState } from 'react';
import { ShieldCheck, LogIn, Eye, EyeOff, AlertCircle, Lock, User } from 'lucide-react';
import { api } from '../services/api';

const ROLE_COLORS = {
  admin:      '#ef4444',
  hr:         '#8b5cf6',
  finance:    '#f59e0b',
  legal:      '#3b82f6',
  operations: '#10b981',
  employee:   '#00f2fe',
};

const ROLE_LABELS = {
  admin:      'System Administrator',
  hr:         'Human Resources',
  finance:    'Finance Department',
  legal:      'Legal & Compliance',
  operations: 'Operations',
  employee:   'Employee',
};

export const LoginPage = ({ onLoginSuccess }) => {
  const [username, setUsername]     = useState('');
  const [password, setPassword]     = useState('');
  const [showPass, setShowPass]     = useState(false);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await api.login(username.trim(), password);
      if (onLoginSuccess) onLoginSuccess(result.user);
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-root">
      {/* Animated background orbs */}
      <div className="login-bg-orb orb-1" />
      <div className="login-bg-orb orb-2" />
      <div className="login-bg-orb orb-3" />

      <div className="login-card">
        {/* Logo + Branding */}
        <div className="login-brand">
          <div className="login-brand-icon">
            <ShieldCheck size={28} style={{ color: '#0a0d16' }} />
          </div>
          <div>
            <h1 className="login-brand-title">POLICY <span>BUDDY</span></h1>
            <p className="login-brand-sub">Enterprise Compliance Assistant</p>
          </div>
        </div>

        <div className="login-divider" />

        <h2 className="login-heading">Sign in to your account</h2>
        <p className="login-subheading">Access is role-restricted. Contact your admin for credentials.</p>

        {/* Error Banner */}
        {error && (
          <div className="login-error-banner">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field-group">
            <label className="login-label">
              <User size={13} />
              Username
            </label>
            <input
              id="login-username"
              type="text"
              className="login-input"
              placeholder="Enter your username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              disabled={loading}
            />
          </div>

          <div className="login-field-group">
            <label className="login-label">
              <Lock size={13} />
              Password
            </label>
            <div className="login-password-wrapper">
              <input
                id="login-password"
                type={showPass ? 'text' : 'password'}
                className="login-input"
                placeholder="Enter your password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                disabled={loading}
              />
              <button
                type="button"
                className="login-show-pass-btn"
                onClick={() => setShowPass(v => !v)}
                tabIndex={-1}
              >
                {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="login-submit-btn"
            disabled={loading || !username.trim() || !password.trim()}
          >
            {loading ? (
              <span className="login-spinner" />
            ) : (
              <>
                <LogIn size={15} />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        {/* Role legend */}
        <div className="login-role-legend">
          <div className="login-legend-title">Available Access Roles</div>
          <div className="login-roles-grid">
            {Object.entries(ROLE_LABELS).map(([role, label]) => (
              <div key={role} className="login-role-chip" style={{ borderColor: ROLE_COLORS[role] + '44' }}>
                <span className="login-role-dot" style={{ background: ROLE_COLORS[role] }} />
                <span className="login-role-name">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="login-default-hint">
          Default admin: <code>admin</code> / <code>admin123</code>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
