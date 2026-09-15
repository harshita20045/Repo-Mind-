import React, { useEffect, useState } from 'react';
import { analyticsApi } from '../lib/api';

export default function AnalyticsPage({ user, memberships }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // For V1, just take the first membership's org. In reality this would be selected.
  const orgId = memberships?.[0]?.organization_id;

  useEffect(() => {
    if (!orgId) {
      setLoading(false);
      return;
    }

    analyticsApi.getOrgAnalytics(orgId)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [orgId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-danger p-6">Error loading analytics: {error}</div>;
  }

  if (!data) {
    return <div className="text-gray-400 p-6">No analytics data available.</div>;
  }

  return (
    <div className="space-y-8 animate-slide-up pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Engineering Intelligence</h1>
        <p className="text-gray-400">Organization-wide risk and review analytics over the last {data.period_days} days.</p>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 shadow-lg">
          <h3 className="text-gray-400 font-medium text-sm mb-4">Total PRs Analyzed</h3>
          <h2 className="text-4xl font-bold text-white">{data.total_reviews}</h2>
        </div>
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 shadow-lg">
          <h3 className="text-gray-400 font-medium text-sm mb-4">Avg Risk Score</h3>
          <div className="flex items-end gap-3">
            <h2 className={`text-4xl font-bold ${data.average_risk_score > 70 ? 'text-danger' : data.average_risk_score > 40 ? 'text-warning' : 'text-success'}`}>
              {data.average_risk_score}
            </h2>
            <span className="text-gray-500 text-sm mb-1">/ 100</span>
          </div>
        </div>
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 shadow-lg">
          <h3 className="text-gray-400 font-medium text-sm mb-4">Critical Vulnerabilities</h3>
          <h2 className="text-4xl font-bold text-danger">{data.findings_by_severity?.critical || 0}</h2>
        </div>
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 shadow-lg">
          <h3 className="text-gray-400 font-medium text-sm mb-4">Persistent Issues</h3>
          <h2 className="text-4xl font-bold text-warning">{data.findings_by_lifecycle?.persistent || 0}</h2>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Finding Severity Distribution */}
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 shadow-lg">
          <h2 className="text-xl font-semibold text-white mb-6">Findings by Severity</h2>
          <div className="space-y-4">
            {['critical', 'high', 'medium', 'low', 'info'].map((sev) => {
              const count = data.findings_by_severity?.[sev] || 0;
              const maxCount = Math.max(...Object.values(data.findings_by_severity || {a:1})) || 1;
              const width = Math.max(5, (count / maxCount) * 100);
              
              const colorClass = sev === 'critical' ? 'bg-danger' : 
                               sev === 'high' ? 'bg-orange-500' :
                               sev === 'medium' ? 'bg-warning' :
                               sev === 'low' ? 'bg-primary' : 'bg-gray-500';

              return (
                <div key={sev} className="flex items-center gap-4">
                  <div className="w-20 text-sm font-medium text-gray-400 capitalize">{sev}</div>
                  <div className="flex-1 bg-surfaceHighlight/30 rounded-full h-3 overflow-hidden border border-white/5">
                    <div className={`h-full ${colorClass} rounded-full`} style={{ width: `${width}%` }}></div>
                  </div>
                  <div className="w-10 text-right text-sm font-bold text-white">{count}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Finding Category Distribution */}
        <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 shadow-lg">
          <h2 className="text-xl font-semibold text-white mb-6">Findings by Category</h2>
          <div className="space-y-4">
            {Object.entries(data.findings_by_category || {}).sort((a,b) => b[1] - a[1]).slice(0, 5).map(([cat, count]) => {
              const maxCount = Math.max(...Object.values(data.findings_by_category || {})) || 1;
              const width = Math.max(5, (count / maxCount) * 100);
              
              return (
                <div key={cat} className="flex items-center gap-4">
                  <div className="w-28 text-sm font-medium text-gray-400 truncate">{cat}</div>
                  <div className="flex-1 bg-surfaceHighlight/30 rounded-full h-3 overflow-hidden border border-white/5">
                    <div className="h-full bg-accent rounded-full" style={{ width: `${width}%` }}></div>
                  </div>
                  <div className="w-10 text-right text-sm font-bold text-white">{count}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      
      {/* Lifecycle Breakdown */}
      <div className="bg-surface/40 backdrop-blur-md rounded-2xl border border-white/5 p-6 shadow-lg">
        <h2 className="text-xl font-semibold text-white mb-6">Resolution Lifecycle</h2>
        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-1 p-5 rounded-xl bg-surfaceHighlight/20 border border-white/5 text-center">
            <h4 className="text-gray-400 font-medium mb-2 uppercase text-xs tracking-wider">New</h4>
            <div className="text-3xl font-bold text-primary">{data.findings_by_lifecycle?.new || 0}</div>
            <p className="text-xs text-gray-500 mt-2">Findings introduced recently</p>
          </div>
          <div className="flex-1 p-5 rounded-xl bg-surfaceHighlight/20 border border-white/5 text-center">
            <h4 className="text-gray-400 font-medium mb-2 uppercase text-xs tracking-wider">Persistent</h4>
            <div className="text-3xl font-bold text-warning">{data.findings_by_lifecycle?.persistent || 0}</div>
            <p className="text-xs text-gray-500 mt-2">Unresolved across multiple review runs</p>
          </div>
          <div className="flex-1 p-5 rounded-xl bg-surfaceHighlight/20 border border-white/5 text-center">
            <h4 className="text-gray-400 font-medium mb-2 uppercase text-xs tracking-wider">Resolved</h4>
            <div className="text-3xl font-bold text-success">{data.findings_by_lifecycle?.resolved || 0}</div>
            <p className="text-xs text-gray-500 mt-2">Issues fixed by developers</p>
          </div>
        </div>
      </div>
    </div>
  );
}
