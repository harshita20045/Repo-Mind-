import React, { useState } from 'react';
import { authApi } from '../lib/api';

export default function LoginForm({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
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
    <div className="w-full max-w-md p-8 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl text-slate-100">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-indigo-600 rounded-lg text-white font-bold text-xl mb-3 shadow-lg shadow-indigo-500/30">
          RM
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          {isRegister ? 'Create your RepoMind account' : 'Sign in to RepoMind'}
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          {isRegister
            ? 'Start reviewing code with grounded AI intelligence'
            : 'Enter your credentials to access your review dashboard'}
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-950/80 border border-red-800/80 text-red-200 text-sm rounded-lg flex items-center gap-2 animate-fadeIn">
          <span className="font-semibold">Error:</span> {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium uppercase tracking-wider text-slate-400 mb-1">
            Email Address
          </label>
          <input
            id="email-input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="developer@company.internal"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
          />
        </div>

        {isRegister && (
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-400 mb-1">
              Organization Name
            </label>
            <input
              id="org-input"
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Engineering / Core Team"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-medium uppercase tracking-wider text-slate-400 mb-1">
            Password
          </label>
          <input
            id="password-input"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
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

      <div className="mt-6 text-center text-xs text-slate-400">
        {isRegister ? (
          <>
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => { setIsRegister(false); setError(null); }}
              className="text-indigo-400 hover:text-indigo-300 font-semibold underline underline-offset-2"
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
              className="text-indigo-400 hover:text-indigo-300 font-semibold underline underline-offset-2"
            >
              Register organization
            </button>
          </>
        )}
      </div>
    </div>
  );
}
