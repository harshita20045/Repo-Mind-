import React from 'react';
import { useQuery } from '@tanstack/react-query';

const StatCard = ({ title, value, icon, trend, isPositive }) => (
  <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 hover:bg-surface/60 transition-colors">
    <div className="flex justify-between items-start mb-4">
      <h3 className="text-gray-400 font-medium text-sm">{title}</h3>
      <div className="p-2 bg-white/5 rounded-lg text-gray-300">
        {icon}
      </div>
    </div>
    <div className="flex items-end gap-3">
      <h2 className="text-3xl font-bold text-white">{value}</h2>
      {trend && (
        <span className={`text-sm font-medium mb-1 ${isPositive ? 'text-success' : 'text-danger'}`}>
          {isPositive ? '+' : '-'}{trend}
        </span>
      )}
    </div>
  </div>
);

const DashboardPage = () => {
  // Placeholder data for the new dashboard
  const stats = [
    {
      title: 'Active Pull Requests',
      value: '24',
      trend: '12%',
      isPositive: true,
      icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>
    },
    {
      title: 'Critical Risk PRs',
      value: '3',
      trend: '2',
      isPositive: false,
      icon: <svg className="w-5 h-5 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
    },
    {
      title: 'Code-Aware Findings',
      value: '156',
      trend: '8%',
      isPositive: true,
      icon: <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
    },
    {
      title: 'Avg Review Time',
      value: '2.4h',
      trend: '1.1h',
      isPositive: true,
      icon: <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    }
  ];

  return (
    <div className="space-y-8 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Company Overview</h1>
          <p className="text-gray-400">Engineering intelligence and PR risk assessment across all repositories.</p>
        </div>
        <button className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors shadow-lg shadow-primary/25 border border-white/10">
          Generate Report
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <StatCard key={i} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Recent Risk Assessments</h2>
          <div className="space-y-4">
            {/* Fake list of PRs */}
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-surfaceHighlight/30 rounded-xl border border-white/5 hover:bg-surfaceHighlight/50 transition-colors cursor-pointer group">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${i === 1 ? 'bg-danger/20 text-danger' : 'bg-success/20 text-success'}`}>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-200 group-hover:text-white transition-colors">Implement Payment Gateway</h4>
                    <p className="text-sm text-gray-400">backend/api • PR #44{i}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${i === 1 ? 'bg-danger/10 text-danger border border-danger/20' : 'bg-success/10 text-success border border-success/20'}`}>
                    {i === 1 ? 'Critical Risk' : 'Low Risk'}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">2 hours ago</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Top Findings</h2>
          <div className="space-y-4">
            {['Hardcoded secret in API', 'Missing unit tests for auth', 'N+1 Query detected', 'Unvalidated external input'].map((finding, i) => (
              <div key={i} className="p-3 rounded-lg bg-surfaceHighlight/30 border border-white/5 flex items-start gap-3">
                <div className="mt-0.5 text-warning">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-300">{finding}</p>
                  <p className="text-xs text-gray-500 mt-1">{5 - i} occurrences</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
