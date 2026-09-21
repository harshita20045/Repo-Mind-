import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useOutletContext } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { authApi } from './lib/api';
import { usePermissions, Permissions } from './hooks/usePermissions';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ReviewPage from './pages/ReviewPage';
import AnalyticsPage from './pages/AnalyticsPage';
import RepositoriesPage from './pages/RepositoriesPage';
import PullRequestsPage from './pages/PullRequestsPage';
import SecurityBrowserPage from './pages/SecurityBrowserPage';
import SettingsPage from './pages/SettingsPage';
import ChatPage from './pages/ChatPage';
import AppLayout from './components/Layout/AppLayout';

const queryClient = new QueryClient();

function ProtectedRoute({ memberships, requiredPermission }) {
  const { can } = usePermissions(memberships);
  if (requiredPermission && !can(requiredPermission)) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center gap-4 animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-danger/10 border border-danger/20 flex items-center justify-center text-danger">
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-bold text-text-primary">Access Denied</h2>
          <p className="text-sm text-text-muted mt-1.5 max-w-xs">You don't have permission to access this page.</p>
        </div>
        <a href="/" className="text-sm font-medium text-primary hover:text-primary-hover transition-colors">
          ← Return to Dashboard
        </a>
      </div>
    );
  }
  const context = useOutletContext();
  return <Outlet context={context} />;
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [memberships, setMemberships] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSession();
  }, []);

  async function checkSession() {
    console.log("checkSession started");
    try {
      const data = await authApi.getMe();
      console.log("checkSession data received:", data);
      if (data && data.user) {
        setCurrentUser(data.user);
        setMemberships(data.memberships || []);
      }
    } catch (err) {
      console.log("checkSession error:", err);
      setCurrentUser(null);
      setMemberships([]);
    } finally {
      console.log("checkSession finally");
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
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        {/* Ambient glow */}
        <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/[0.05] blur-[120px] pointer-events-none" />
        <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent/[0.04] blur-[120px] pointer-events-none" />
        {/* Logo */}
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-glow-primary">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        {/* Spinner */}
        <svg className="animate-spin w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
          <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <p className="text-sm text-text-muted font-medium">Connecting to RepoMind…</p>
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
          <Route element={<AppLayout user={currentUser} memberships={memberships} onLogout={handleLogout} />}>
            <Route path="/" element={<DashboardPage />} />
            
            <Route element={<ProtectedRoute memberships={memberships} requiredPermission={Permissions.REPOS_READ} />}>
              <Route path="/repositories" element={<RepositoriesPage />} />
              <Route path="/repositories/:rid/pull-requests" element={<PullRequestsPage />} />
              <Route path="/repositories/:rid/pull-requests/:prid" element={<ReviewPage user={currentUser} memberships={memberships} onLogout={handleLogout} />} />
            </Route>

            <Route element={<ProtectedRoute memberships={memberships} requiredPermission={Permissions.SECURITY_READ} />}>
              <Route path="/security" element={<SecurityBrowserPage />} />
            </Route>

            <Route element={<ProtectedRoute memberships={memberships} requiredPermission={Permissions.ANALYTICS_READ} />}>
              <Route path="/analytics" element={<AnalyticsPage user={currentUser} memberships={memberships} />} />
            </Route>

            <Route element={<ProtectedRoute memberships={memberships} requiredPermission={Permissions.CHAT_USE} />}>
              <Route path="/chat" element={<ChatPage user={currentUser} memberships={memberships} />} />
            </Route>

            <Route element={<ProtectedRoute memberships={memberships} requiredPermission={Permissions.ORG_UPDATE} />}>
              <Route path="/settings" element={<SettingsPage user={currentUser} />} />
            </Route>
            
          </Route>
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
