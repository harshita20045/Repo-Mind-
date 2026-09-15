import React from 'react';

export default function RiskAssessment({ riskData }) {
  if (!riskData) {
    return <div className="text-gray-400 p-8 text-center">No risk assessment data available for this run.</div>;
  }

  const {
    risk_score,
    security_risk_level,
    architecture_risk_level,
    test_gap_level,
    blast_radius_modules,
    explanation
  } = riskData;

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical':
      case 'high': return 'text-danger bg-danger/10 border-danger/20';
      case 'medium': return 'text-warning bg-warning/10 border-warning/20';
      case 'low': return 'text-success bg-success/10 border-success/20';
      default: return 'text-gray-300 bg-white/5 border-white/10';
    }
  };

  const getTextColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical':
      case 'high': return 'text-danger';
      case 'medium': return 'text-warning';
      case 'low': return 'text-success';
      default: return 'text-gray-300';
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header section */}
      <div className="flex flex-col md:flex-row gap-8 items-center bg-surfaceHighlight/20 p-6 rounded-2xl border border-white/5">
        <div className="relative flex-shrink-0">
          <svg className="w-32 h-32 transform -rotate-90">
            <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-surfaceHighlight/50" />
            <circle 
              cx="64" cy="64" r="56" 
              stroke="currentColor" 
              strokeWidth="12" 
              fill="transparent" 
              strokeDasharray={351.8} 
              strokeDashoffset={351.8 - (351.8 * (risk_score || 0)) / 100}
              className={`transition-all duration-1000 ${
                risk_score > 70 ? 'text-danger' : risk_score > 40 ? 'text-warning' : 'text-success'
              }`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold text-white">{risk_score || 0}</span>
            <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Risk Score</span>
          </div>
        </div>
        
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-white mb-3">Overall Structural Risk</h2>
          <p className="text-gray-300 leading-relaxed text-sm">
            {explanation || "The risk engine analyzed the structural changes in this PR and computed an aggregate risk score based on blast radius, security implications, and test coverage gaps."}
          </p>
        </div>
      </div>

      {/* Breakdown Metrics */}
      <h3 className="text-lg font-semibold text-white mb-4 mt-8">Risk Vectors</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 rounded-xl bg-surface/50 border border-white/5">
          <div className="flex justify-between items-center mb-3">
            <span className="text-gray-400 font-medium">Security</span>
            <span className={`px-2 py-1 rounded text-xs font-bold border capitalize ${getRiskColor(security_risk_level)}`}>
              {security_risk_level || 'Unknown'}
            </span>
          </div>
          <p className="text-xs text-gray-500">Risk derived from secrets, auth changes, and injection vulnerabilities.</p>
        </div>

        <div className="p-5 rounded-xl bg-surface/50 border border-white/5">
          <div className="flex justify-between items-center mb-3">
            <span className="text-gray-400 font-medium">Architecture</span>
            <span className={`px-2 py-1 rounded text-xs font-bold border capitalize ${getRiskColor(architecture_risk_level)}`}>
              {architecture_risk_level || 'Unknown'}
            </span>
          </div>
          <p className="text-xs text-gray-500">Risk derived from core structural modifications or deep dependencies.</p>
        </div>

        <div className="p-5 rounded-xl bg-surface/50 border border-white/5">
          <div className="flex justify-between items-center mb-3">
            <span className="text-gray-400 font-medium">Test Gap</span>
            <span className={`px-2 py-1 rounded text-xs font-bold border capitalize ${getRiskColor(test_gap_level)}`}>
              {test_gap_level || 'Unknown'}
            </span>
          </div>
          <p className="text-xs text-gray-500">Measures the lack of accompanying tests for new critical logic.</p>
        </div>
      </div>

      {/* Blast Radius */}
      <h3 className="text-lg font-semibold text-white mb-4 mt-8">Blast Radius Analysis</h3>
      <div className="p-6 rounded-xl bg-surfaceHighlight/20 border border-white/5">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-full bg-accent/20 text-accent flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
            </svg>
          </div>
          <div>
            <h4 className="text-white font-medium">Impacted Modules</h4>
            <p className="text-sm text-gray-400">Files and services potentially affected by these changes.</p>
          </div>
        </div>
        
        {blast_radius_modules && blast_radius_modules.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {blast_radius_modules.map((module, i) => (
              <span key={i} className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-md text-sm text-gray-300 font-mono">
                {module}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 italic">No significant multi-module blast radius detected.</p>
        )}
      </div>
    </div>
  );
}
