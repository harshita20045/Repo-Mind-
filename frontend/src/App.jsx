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
      <div className="flex flex-col items-center justify-center h-full text-center space-y-4 text-slate-300">
        <svg className="w-16 h-16 text-danger/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h2 className="text-2xl font-bold">Access Denied</h2>
        <p className="text-slate-400">You don't have permission to access this page.</p>
        <a href="/" className="text-indigo-400 hover:text-indigo-300 transition-colors">Return to Dashboard</a>
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
