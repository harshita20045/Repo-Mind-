const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Ensures HttpOnly auth cookies are sent and received
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    let errorMsg = data?.detail || `Request failed with status ${response.status}`;
    if (response.status === 403) {
      errorMsg = "You don't have permission to perform this action.";
    } else if (response.status === 401) {
      errorMsg = "Authentication required. Please log in again.";
    }
    const err = new Error(errorMsg);
    err.status = response.status;
    throw err;
  }

  return data;
}

export const authApi = {
  login: (email, password) =>
    apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (email, password, organization_name) =>
    apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, organization_name }),
    }),
  logout: () =>
    apiRequest('/auth/logout', {
      method: 'POST',
    }),
  getMe: () =>
    apiRequest('/auth/me', {
      method: 'GET',
    }),
  onboard: (invitation_token, new_password) =>
    apiRequest('/auth/onboard', {
      method: 'POST',
      body: JSON.stringify({ invitation_token, new_password }),
    }),
};

export const reviewApi = {
  triggerReview: (prId) =>
    apiRequest(`/pull-requests/${prId}/review`, {
      method: 'POST',
    }),
  getReviewRun: (runId) =>
    apiRequest(`/review-runs/${runId}`, {
      method: 'GET',
    }),
  listReviewRuns: (prId) =>
    apiRequest(`/pull-requests/${prId}/review-runs`, {
      method: 'GET',
    }),
  approveReviewRun: (runId, decisionData) =>
    apiRequest(`/review-runs/${runId}/decide`, {
      method: 'POST',
      body: JSON.stringify(decisionData),
    }),
};

export const orgApi = {
  getOrganization: (orgId) =>
    apiRequest(`/organizations/${orgId}`, {
      method: 'GET',
    }),
  createOrganization: (name) =>
    apiRequest(`/organizations`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  getProjects: (orgId) =>
    apiRequest(`/organizations/${orgId}/projects`, {
      method: 'GET',
    }),
  getRepositories: (projectId) =>
    apiRequest(`/projects/${projectId}/repositories`, {
      method: 'GET',
    }),
  getRepository: (repoId) =>
    apiRequest(`/repositories/${repoId}`, {
      method: 'GET',
    }),
  createProject: (orgId, name) =>
    apiRequest(`/organizations/${orgId}/projects`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  inviteMember: (orgId, email, role) =>
    apiRequest(`/organizations/${orgId}/members`, {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    }),
  updateMemberRole: (orgId, targetUserId, role) =>
    apiRequest(`/organizations/${orgId}/members/${targetUserId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    }),
  removeMember: (orgId, targetUserId) =>
    apiRequest(`/organizations/${orgId}/members/${targetUserId}`, {
      method: 'DELETE',
    }),
  connectRepository: (orgId, payload) =>
    apiRequest(`/repositories/connect?organization_id=${orgId}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  triggerIndex: (repoId) =>
    apiRequest(`/repositories/${repoId}/index`, {
      method: 'POST',
    }),
  getTeams: (orgId) =>
    apiRequest(`/organizations/${orgId}/teams`, {
      method: 'GET',
    }),
  createTeam: (orgId, name, description) =>
    apiRequest(`/organizations/${orgId}/teams`, {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    }),
};

export const githubApi = {
  getPullRequests: (repoId) =>
    apiRequest(`/repositories/${repoId}/pull-requests`, {
      method: 'GET',
    }),
  syncRepositoryPullRequests: (repoId) =>
    apiRequest(`/repositories/${repoId}/pull-requests?sync=true`, {
      method: 'GET',
    }),
  getPullRequest: (prId) =>
    apiRequest(`/pull-requests/${prId}`, {
      method: 'GET',
    }),
  getPullRequestEvents: (prId) =>
    apiRequest(`/pull-requests/${prId}/events`, {
      method: 'GET',
    }),
  getOAuthLoginUrl: () =>
    apiRequest(`/oauth/login`, {
      method: 'GET',
    }),
  unlinkGitHub: () =>
    apiRequest(`/oauth/unlink`, {
      method: 'DELETE',
    }),
  syncPullRequest: (prId) =>
    apiRequest(`/pull-requests/${prId}/sync`, {
      method: 'POST',
    }),
  mergePullRequest: (prId) =>
    apiRequest(`/pull-requests/${prId}/merge`, {
      method: 'POST',
    }),
  reopenPullRequest: (prId) =>
    apiRequest(`/pull-requests/${prId}/reopen`, {
      method: 'POST',
    }),
  getMergePolicy: (repoId) =>
    apiRequest(`/repositories/${repoId}/merge-policy`, {
      method: 'GET',
    }),
  updateMergePolicy: (repoId, policyData) =>
    apiRequest(`/repositories/${repoId}/merge-policy`, {
      method: 'PUT',
      body: JSON.stringify(policyData),
    }),
};

export const analyticsApi = {
  getOrgAnalytics: (orgId, days = 30) =>
    apiRequest(`/analytics/organization/${orgId}?days=${days}`, {
      method: 'GET',
    }),
};

export const chatApi = {
  createSession: (data) =>
    apiRequest('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getSessions: (orgId, contextType, contextId) =>
    apiRequest(`/chat/sessions?organization_id=${orgId}&context_type=${contextType}&context_id=${contextId}`, {
      method: 'GET',
    }),
  getHistory: (sessionId, orgId) =>
    apiRequest(`/chat/sessions/${sessionId}/messages?organization_id=${orgId}`, {
      method: 'GET',
    }),
  sendMessage: (sessionId, orgId, data) =>
    apiRequest(`/chat/sessions/${sessionId}/messages?organization_id=${orgId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};



export const securityApi = {
  getFindings: (orgId, severity = '', status = '') =>
    apiRequest(`/security/findings?org_id=${orgId}${severity ? `&severity=${severity}` : ''}${status ? `&status=${status}` : ''}`, {
      method: 'GET',
    }),
  updateFindingStatus: (findingId, status) =>
    apiRequest(`/security/findings/${findingId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    }),
};
