import React, { useState } from 'react';
import { authApi } from '../lib/api';

export default function LoginForm({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const validatePassword = (pwd) => {
    if (pwd.length <= 8) return "Password must be greater than 8 characters.";
    if (!/[A-Z]/.test(pwd)) return "Password must contain at least one uppercase letter.";
    if (!/[a-z]/.test(pwd)) return "Password must contain at least one lowercase letter.";
    if (!/[0-9]/.test(pwd)) return "Password must contain at least one number.";
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) return "Password must contain at least one special character.";
    return null;
  };

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    const pwdError = validatePassword(password);
    if (pwdError) {
      setError(pwdError);
      return;
    }

    setLoading(true);

    try {
      let data;
      if (isRegister) {
        data = await authApi.register(email, password, orgName || 'Default Org');
      } else {
        data = await authApi.login(email, password);
      }
      onLoginSuccess(data);
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md p-8 bg-surface/50 backdrop-blur-xl border border-white/5 rounded-2xl shadow-2xl z-10 animate-slide-up">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-tr from-primary to-accent rounded-xl text-white font-bold text-xl mb-4 shadow-lg shadow-primary/20">
          RM
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          {isRegister ? 'Create your account' : 'Welcome back'}
        </h2>
        <p className="text-sm text-gray-400 mt-2">
          {isRegister
            ? 'Start reviewing code with grounded AI intelligence'
            : 'Enter your credentials to access your dashboard'}
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl flex items-center gap-3 animate-fade-in">
          <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-medium">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">
            Email Address
          </label>
          <input
            id="email-input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="developer@company.com"
            className="w-full px-4 py-2.5 bg-surfaceHighlight/30 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent text-sm transition-all"
          />
        </div>

        {isRegister && (
          <div className="animate-fade-in">
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">
              Organization Name
            </label>
            <input
              id="org-input"
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Engineering / Core Team"
              className="w-full px-4 py-2.5 bg-surfaceHighlight/30 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent text-sm transition-all"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">
            Password
          </label>
          <input
            id="password-input"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-4 py-2.5 bg-surfaceHighlight/30 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent text-sm transition-all"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-4 py-3 px-4 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white font-medium rounded-xl text-sm transition-all shadow-lg shadow-primary/25 flex items-center justify-center gap-2 border border-white/10"
        >
          {loading && (
            <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
          )}
          {isRegister ? (loading ? 'Creating account...' : 'Create Account') : (loading ? 'Signing in...' : 'Sign In')}
        </button>
      </form>

      <div className="mt-8 text-center text-sm text-gray-400">
        {isRegister ? (
          <>
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => { setIsRegister(false); setError(null); }}
              className="text-primary hover:text-primary-hover font-medium transition-colors"
            >
              Sign in
            </button>
          </>
        ) : (
          <>
            New organization or team?{' '}
            <button
              type="button"
              onClick={() => { setIsRegister(true); setError(null); }}
              className="text-primary hover:text-primary-hover font-medium transition-colors"
            >
              Register organization
            </button>
          </>
        )}
      </div>
    </div>
  );
}
