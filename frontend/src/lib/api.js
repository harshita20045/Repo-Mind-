const API_BASE = 'http://localhost:8000';

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
  approveReviewRun: (runId, decisionData) =>
    apiRequest(`/review-runs/${runId}/approve`, {
      method: 'POST',
      body: JSON.stringify(decisionData),
    }),
};

export const orgApi = {
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
  connectRepository: (orgId, payload) =>
    apiRequest(`/repositories/connect?organization_id=${orgId}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  triggerIndex: (repoId) =>
    apiRequest(`/repositories/${repoId}/index`, {
      method: 'POST',
    }),
};

export const githubApi = {
  getPullRequests: (repoId) =>
    apiRequest(`/repositories/${repoId}/pull-requests`, {
      method: 'GET',
    }),
  getPullRequest: (prId) =>
    apiRequest(`/pull-requests/${prId}`, {
      method: 'GET',
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

export const mlApi = {
  getPrPrediction: (prId) =>
    apiRequest(`/ml/prediction/pr/${prId}`, {
      method: 'GET',
    }),
};
