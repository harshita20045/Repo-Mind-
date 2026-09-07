import React, { useState, useEffect } from 'react';
import { authApi } from './lib/api';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [memberships, setMemberships] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSession();
  }, []);

  async function checkSession() {
    try {
      const data = await authApi.getMe();
      if (data && data.user) {
        setCurrentUser(data.user);
        setMemberships(data.memberships || []);
      }
    } catch {
      // Unauthenticated - show login page
      setCurrentUser(null);
      setMemberships([]);
    } finally {
      setLoading(false);
    }
  }

  function handleLoginSuccess(authData) {
    setCurrentUser(authData.user);
    setMemberships(authData.memberships || []);
  }

  function handleLogout() {
    setCurrentUser(null);
    setMemberships([]);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300">
        <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full mb-4"></div>
        <p className="text-sm font-medium tracking-wide text-slate-400">Loading RepoMind session...</p>
      </div>
    );
  }

  if (!currentUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <DashboardPage
      user={currentUser}
      memberships={memberships}
      onLogout={handleLogout}
    />
  );
}
