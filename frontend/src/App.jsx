import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { authApi } from './lib/api';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ReviewPage from './pages/ReviewPage';
import AnalyticsPage from './pages/AnalyticsPage';
import RepositoriesPage from './pages/RepositoriesPage';
import MyPRsPage from './pages/MyPRsPage';
import SecurityBrowserPage from './pages/SecurityBrowserPage';
import SettingsPage from './pages/SettingsPage';
import AppLayout from './components/Layout/AppLayout';

const queryClient = new QueryClient();

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
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout user={currentUser} memberships={memberships} />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/repositories" element={<RepositoriesPage />} />
            <Route path="/prs" element={<MyPRsPage />} />
            <Route path="/security" element={<SecurityBrowserPage />} />
            <Route path="/settings" element={<SettingsPage user={currentUser} />} />
            <Route path="/repositories/:rid/pull-requests/:prid" element={<ReviewPage user={currentUser} memberships={memberships} onLogout={handleLogout} />} />
            <Route path="/analytics" element={<AnalyticsPage user={currentUser} memberships={memberships} />} />
          </Route>
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
