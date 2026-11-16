import React, { useState } from 'react';
import { SeverityBadge } from '../ui/Badge';
import { Button } from '../ui/Button';
import Modal from '../ui/Modal';

export default function ArchitectureRuleManager({
  rules = [],
  onCreateRule,
  onUpdateRule,
  onDeleteRule,
  onResetRules,
  isMutating = false,
}) {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    rule_code: '',
    name: '',
    description: '',
    rule_type: 'forbidden_dependency',
    source_layer: 'presentation',
    target_layer: 'data_access',
    source_pattern: '',
    target_pattern: '',
    severity: 'high',
    suggested_fix: '',
  });

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    if (!formData.rule_code || !formData.name) return;
    onCreateRule(formData);
    setIsAddModalOpen(false);
    setFormData({
      rule_code: '',
      name: '',
      description: '',
      rule_type: 'forbidden_dependency',
      source_layer: 'presentation',
      target_layer: 'data_access',
      source_pattern: '',
      target_pattern: '',
      severity: 'high',
      suggested_fix: '',
    });
  };

  return (
    <div className="space-y-4">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface border border-border rounded-lg p-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">
            Architecture Rules Governance
          </h3>
          <p className="text-[12px] text-text-secondary mt-0.5">
            Configure, customize, or toggle architecture boundary and layer separation rules.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={onResetRules}
            disabled={isMutating}
            className="text-xs"
          >
            Reset Defaults
          </Button>
          <Button
            variant="primary"
            onClick={() => setIsAddModalOpen(true)}
            disabled={isMutating}
            className="text-xs"
          >
            + Add Custom Rule
          </Button>
        </div>
      </div>

      {/* Rules Table */}
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surfaceHighlight/50 border-b border-border text-text-muted uppercase text-[10px] tracking-wider">
              <tr>
                <th className="p-3">Status</th>
                <th className="p-3">Code</th>
                <th className="p-3">Rule Name & Details</th>
                <th className="p-3">Type</th>
                <th className="p-3">Severity</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-3">
                    <button
                      type="button"
                      onClick={() => onUpdateRule(rule.id, { is_enabled: !rule.is_enabled })}
                      disabled={isMutating}
                      className={`relative inline-flex h-4 w-7 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        rule.is_enabled ? 'bg-primary' : 'bg-surfaceHighlight'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          rule.is_enabled ? 'translate-x-3' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </td>
                  <td className="p-3 font-mono font-bold text-text-primary">
                    {rule.rule_code}
                  </td>
                  <td className="p-3 max-w-md">
                    <div className="font-semibold text-text-primary mb-0.5">{rule.name}</div>
                    <div className="text-[11px] text-text-muted line-clamp-2">{rule.description}</div>
                    {rule.source_layer && rule.target_layer && (
                      <div className="mt-1 flex items-center gap-1 font-mono text-[10px] text-text-secondary">
                        <span className="bg-surfaceHighlight px-1.5 py-0.2 rounded border border-border">{rule.source_layer}</span>
                        <span>→ ❌ →</span>
                        <span className="bg-surfaceHighlight px-1.5 py-0.2 rounded border border-border">{rule.target_layer}</span>
                      </div>
                    )}
                  </td>
                  <td className="p-3 font-mono text-[10px] uppercase text-text-muted">
                    {rule.rule_type?.replace(/_/g, ' ')}
                  </td>
                  <td className="p-3">
                    <SeverityBadge severity={rule.severity} />
                  </td>
                  <td className="p-3 text-right">
                    {!rule.is_system_inferred && (
                      <button
                        type="button"
                        onClick={() => onDeleteRule(rule.id)}
                        disabled={isMutating}
                        className="text-danger hover:text-danger-hover text-xs font-semibold"
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Custom Rule Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Create Custom Architecture Rule"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <div>
            <label htmlFor="rule_code" className="block text-text-muted font-medium mb-1">Rule Code (e.g. CUSTOM-001)</label>
            <input
              id="rule_code"
              type="text"
              required
              value={formData.rule_code}
              onChange={(e) => setFormData({ ...formData, rule_code: e.target.value })}
              className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label htmlFor="rule_name" className="block text-text-muted font-medium mb-1">Rule Name</label>
            <input
              id="rule_name"
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label htmlFor="rule_type" className="block text-text-muted font-medium mb-1">Rule Type</label>
            <select
              id="rule_type"
              value={formData.rule_type}
              onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}
              className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
            >
              <option value="forbidden_dependency">Forbidden Dependency</option>
              <option value="layer_boundary">Layer Boundary Enforcement</option>
              <option value="api_db_isolation">API to Database Isolation</option>
              <option value="no_circular_dependencies">No Circular Dependencies</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="source_layer" className="block text-text-muted font-medium mb-1">Source Layer</label>
              <select
                id="source_layer"
                value={formData.source_layer}
                onChange={(e) => setFormData({ ...formData, source_layer: e.target.value })}
                className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="presentation">Presentation</option>
                <option value="business_logic">Business Logic</option>
                <option value="domain">Domain</option>
                <option value="data_access">Data Access</option>
                <option value="infrastructure">Infrastructure</option>
                <option value="shared_utility">Shared Utility</option>
                <option value="frontend_ui">Frontend UI</option>
              </select>
            </div>
            <div>
              <label htmlFor="target_layer" className="block text-text-muted font-medium mb-1">Target Layer</label>
              <select
                id="target_layer"
                value={formData.target_layer}
                onChange={(e) => setFormData({ ...formData, target_layer: e.target.value })}
                className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="data_access">Data Access</option>
                <option value="infrastructure">Infrastructure</option>
                <option value="presentation">Presentation</option>
                <option value="business_logic">Business Logic</option>
                <option value="domain">Domain</option>
                <option value="backend">Backend (all)</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="rule_severity" className="block text-text-muted font-medium mb-1">Severity</label>
            <select
              id="rule_severity"
              value={formData.severity}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
              className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label htmlFor="rule_description" className="block text-text-muted font-medium mb-1">Description / Rationale</label>
            <textarea
              id="rule_description"
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label htmlFor="rule_suggested_fix" className="block text-text-muted font-medium mb-1">Suggested Fix / Remediation</label>
            <input
              id="rule_suggested_fix"
              type="text"
              value={formData.suggested_fix}
              onChange={(e) => setFormData({ ...formData, suggested_fix: e.target.value })}
              placeholder="e.g. Delegate call via service interface"
              className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={isMutating}>
              Save Rule
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
