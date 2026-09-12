import React, { useState } from 'react';
import { ShieldCheck, LogIn, Eye, EyeOff, AlertCircle, Lock, User, Mail } from 'lucide-react';
import { api } from '../services/api';

const ROLE_COLORS = {
  admin:      '#ef4444',
  hr:         '#8b5cf6',
  employee:   '#00f2fe',
};

const ROLE_LABELS = {
  admin:      'System Administrator',
  hr:         'Human Resources',
  employee:   'Standard Employee',
};

export const LoginPage = ({ onLoginSuccess }) => {
  const [password, setPassword]     = useState('');
  const [name, setName]             = useState('');
  const [email, setEmail]           = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [showPass, setShowPass]     = useState(false);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const activeUser = email.trim();
    if (!activeUser || !password.trim() || (isRegistering && (!name.trim() || !confirmPassword.trim()))) {
      setError('Please fill all required fields.');
      return;
    }
    if (isRegistering && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      if (isRegistering) {
        await api.register(activeUser, password, name.trim(), activeUser);
      }
      const result = await api.login(activeUser, password);
      if (onLoginSuccess) onLoginSuccess(result.user);
    } catch (err) {
      setError(err.message || (isRegistering ? 'Registration failed. Please try again.' : 'Invalid credentials. Please try again.'));
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

        <h2 className="login-heading">{isRegistering ? "Create an account" : "Sign in to your account"}</h2>
        <p className="login-subheading">
          {isRegistering 
            ? "Sign up to access the Enterprise Compliance Assistant." 
            : "Access is role-restricted. Contact your admin for credentials."}
        </p>

        {/* Error Banner */}
        {error && (
          <div className="login-error-banner">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          {isRegistering && (
            <div className="login-field-group">
              <label className="login-label">
                <User size={13} />
                Full Name
              </label>
              <input
                id="login-name"
                type="text"
                className="login-input"
                placeholder="Enter your full name"
                value={name}
                onChange={e => setName(e.target.value)}
                autoComplete="name"
                disabled={loading}
              />
            </div>
          )}

          <div className="login-field-group">
            <label className="login-label">
              <Mail size={13} />
              Email Address
            </label>
            <input
              id="login-email"
              type="text"
              className="login-input"
              placeholder="Enter your email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              autoFocus
              disabled={loading}
            />
          </div>

          <div className="login-field-group">
            <label className="login-label">
              <Lock size={13} />
              {isRegistering ? "Create Password" : "Password"}
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

          {isRegistering && (
            <div className="login-field-group">
              <label className="login-label">
                <Lock size={13} />
                Confirm Password
              </label>
              <div className="login-password-wrapper">
                <input
                  id="login-confirm-password"
                  type={showPass ? 'text' : 'password'}
                  className="login-input"
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                  disabled={loading}
                />
              </div>
            </div>
          )}

          <button
            id="login-submit-btn"
            type="submit"
            className="login-submit-btn"
            disabled={loading || !password.trim() || !email.trim() || (isRegistering && (!name.trim() || !confirmPassword.trim()))}
          >
            {loading ? (
              <span className="login-spinner" />
            ) : (
              <>
                <LogIn size={15} />
                <span>{isRegistering ? "Sign Up" : "Sign In"}</span>
              </>
            )}
          </button>

          <div style={{ textAlign: "center", marginTop: "1rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            {isRegistering ? "Already have an account? " : "Don't have an account? "}
            <button 
              type="button" 
              onClick={() => { setIsRegistering(!isRegistering); setError(''); }}
              style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontWeight: "600" }}
            >
              {isRegistering ? "Sign In" : "Sign Up"}
            </button>
          </div>
        </form>


      </div>
    </div>
  );
};

export default LoginPage;
