import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../lib/api';

const StatCard = ({ title, value, icon, isPositive }) => (
  <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 hover:bg-surface/60 transition-colors">
    <div className="flex justify-between items-start mb-4">
      <h3 className="text-gray-400 font-medium text-sm">{title}</h3>
      <div className="p-2 bg-white/5 rounded-lg text-gray-300">
        {icon}
      </div>
    </div>
    <div className="flex items-end gap-3">
      <h2 className="text-3xl font-bold text-white">{value}</h2>
    </div>
  </div>
);

const DashboardPage = () => {
  const { memberships } = useOutletContext();
  const orgId = memberships?.[0]?.organization_id;

  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['orgAnalytics', orgId],
    queryFn: () => analyticsApi.getOrgAnalytics(orgId, 30),
    enabled: !!orgId,
  });

  const stats = [
    {
      title: 'Total PRs Reviewed (30d)',
      value: analytics?.total_reviews || 0,
      icon: <svg className="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>
    },
    {
      title: 'Average Risk Score',
      value: analytics?.average_risk_score || 0,
      icon: <svg className="w-5 h-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
    },
    {
      title: 'Critical Findings',
      value: analytics?.findings_by_severity?.critical || 0,
      icon: <svg className="w-5 h-5 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
    },
    {
      title: 'Security Findings',
      value: analytics?.findings_by_category?.security || 0,
      icon: <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
    }
  ];

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] text-gray-400">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
        Loading dashboard data...
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Company Overview</h1>
          <p className="text-gray-400">Engineering intelligence and PR risk assessment across all repositories.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <StatCard key={i} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Findings by Severity</h2>
          <div className="space-y-4">
            {Object.entries(analytics?.findings_by_severity || {}).length === 0 && (
              <p className="text-gray-400">No findings in the last 30 days.</p>
            )}
            {Object.entries(analytics?.findings_by_severity || {}).map(([severity, count]) => (
              <div key={severity} className="flex justify-between items-center p-3 rounded-lg bg-surfaceHighlight/30 border border-white/5">
                <span className="capitalize text-gray-300">{severity}</span>
                <span className="font-bold text-white">{count}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Findings by Category</h2>
          <div className="space-y-4">
            {Object.entries(analytics?.findings_by_category || {}).length === 0 && (
              <p className="text-gray-400">No findings in the last 30 days.</p>
            )}
            {Object.entries(analytics?.findings_by_category || {}).map(([category, count]) => (
              <div key={category} className="flex justify-between items-center p-3 rounded-lg bg-surfaceHighlight/30 border border-white/5">
                <span className="capitalize text-gray-300">{category}</span>
                <span className="font-bold text-white">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
