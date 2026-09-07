import React from 'react';
import { authApi } from '../lib/api';
import MemberManagement from '../components/MemberManagement';

export default function DashboardPage({ user, memberships, onLogout }) {
  async function handleLogout() {
    try {
      await authApi.logout();
    } catch (err) {
      console.error('Logout error', err);
    } finally {
      onLogout();
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center font-bold text-white shadow-md shadow-indigo-600/30">
            RM
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-none">RepoMind</h1>
            <span className="text-xs text-slate-400">Intelligence Platform</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-semibold text-slate-200">{user.email}</p>
            <p className="text-[11px] text-slate-400">
              Role: <span className="text-indigo-400 font-medium">{memberships[0]?.role || 'member'}</span>
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-8 space-y-8">
        <div className="bg-gradient-to-r from-indigo-900/30 via-slate-900 to-slate-900 border border-indigo-500/20 p-6 rounded-2xl shadow-xl">
          <h2 className="text-2xl font-bold text-white mb-2">Welcome back</h2>
          <p className="text-slate-400 text-sm max-w-2xl">
            You are signed in as <span className="text-white font-medium">{user.email}</span>. Your authenticated session is active via secure HttpOnly cookie.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-xl space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Organization Memberships
            </h3>
            {memberships.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No organizations joined yet.</p>
            ) : (
              <div className="space-y-3">
                {memberships.map((m) => (
                  <div key={m.id} className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-lg flex flex-col gap-3">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm font-semibold text-white">{m.organization.name}</p>
                        <p className="text-xs text-slate-400">Org ID: #{m.organization_id}</p>
                      </div>
                      <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800/60">
                        {m.role}
                      </span>
                    </div>
                    <MemberManagement organizationId={m.organization_id} currentUserRole={m.role} />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-xl space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              Milestone Status
            </h3>
            <div className="space-y-2.5 text-xs text-slate-300">
              <div className="flex justify-between p-2 bg-slate-800/40 rounded border border-slate-800">
                <span>M0: Foundation & Database</span>
                <span className="text-emerald-400 font-semibold">VERIFIED PASS</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-800/40 rounded border border-slate-800">
                <span>M1: Auth & User Management</span>
                <span className="text-emerald-400 font-semibold">IMPLEMENTED</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-800/40 rounded border border-slate-800 opacity-60">
                <span>M2: Organization/Project/Repo Hierarchy</span>
                <span className="text-slate-400">NEXT</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
