import React, { useEffect, useState } from 'react';

export default function MemberManagement({ organizationId, currentUserRole }) {
  const [members, setMembers] = useState([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('developer');
  const [error, setError] = useState(null);

  const isAdmin = currentUserRole === 'org_admin';

  useEffect(() => {
    fetchMembers();
  }, [organizationId]);

  async function fetchMembers() {
    try {
      const res = await fetch(`/api/organizations/${organizationId}/members`);
      if (res.ok) {
        const data = await res.json();
        setMembers(data);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleInvite(e) {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch(`/api/organizations/${organizationId}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: inviteEmail, role: inviteRole })
      });
      if (!res.ok) {
        const err = await res.json();
        setError(err.detail || 'Failed to invite');
        return;
      }
      setInviteEmail('');
      fetchMembers();
    } catch (e) {
      setError('An error occurred');
    }
  }

  async function handleUpdateRole(userId, newRole) {
    try {
      const res = await fetch(`/api/organizations/${organizationId}/members/${userId}/role`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
      });
      if (res.ok) {
        fetchMembers();
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to update role');
      }
    } catch (e) {
      alert('Error updating role');
    }
  }

  async function handleRemove(userId) {
    if (!confirm('Are you sure you want to remove this member?')) return;
    try {
      const res = await fetch(`/api/organizations/${organizationId}/members/${userId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchMembers();
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to remove member');
      }
    } catch (e) {
      alert('Error removing member');
    }
  }

  if (!isAdmin) {
    return (
      <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-xl mt-6">
        <h3 className="text-base font-semibold text-white mb-4">Organization Members</h3>
        <div className="space-y-2 text-sm text-slate-300">
          {members.map(m => (
            <div key={m.id} className="flex justify-between items-center p-2 bg-slate-800/40 rounded border border-slate-800">
              <span>{m.email}</span>
              <span className="text-xs px-2 py-1 bg-slate-700 rounded text-slate-300">{m.role}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-xl mt-6">
      <h3 className="text-base font-semibold text-white mb-4">Manage Organization Members</h3>
      
      {error && <div className="text-red-400 text-sm mb-4 bg-red-900/20 p-2 rounded">{error}</div>}

      <form onSubmit={handleInvite} className="flex gap-2 mb-6">
        <input 
          type="email" 
          value={inviteEmail}
          onChange={e => setInviteEmail(e.target.value)}
          placeholder="User Email" 
          required 
          className="bg-slate-800 border border-slate-700 text-sm rounded px-3 py-1.5 flex-1 focus:outline-none focus:border-indigo-500 text-white"
        />
        <select 
          value={inviteRole}
          onChange={e => setInviteRole(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-sm rounded px-3 py-1.5 focus:outline-none focus:border-indigo-500 text-white"
        >
          <option value="developer">Developer</option>
          <option value="reviewer">Reviewer</option>
          <option value="team_lead">Team Lead</option>
          <option value="org_admin">Org Admin</option>
        </select>
        <button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-1.5 rounded font-medium transition">
          Add
        </button>
      </form>

      <div className="space-y-2">
        {members.map(m => (
          <div key={m.id} className="flex justify-between items-center p-3 bg-slate-800/60 rounded border border-slate-700/60">
            <span className="text-sm text-slate-200">{m.email}</span>
            <div className="flex gap-2 items-center">
              <select 
                value={m.role}
                onChange={e => handleUpdateRole(m.user_id, e.target.value)}
                className="bg-slate-900 border border-slate-700 text-xs rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="developer">Developer</option>
                <option value="reviewer">Reviewer</option>
                <option value="team_lead">Team Lead</option>
                <option value="org_admin">Org Admin</option>
              </select>
              <button 
                onClick={() => handleRemove(m.user_id)}
                className="text-red-400 hover:text-red-300 text-xs font-medium px-2 py-1 bg-red-400/10 hover:bg-red-400/20 rounded transition"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
