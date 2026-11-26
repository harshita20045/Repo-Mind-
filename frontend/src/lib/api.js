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
      errorMsg = data?.detail || "You don't have permission to perform this action.";
    } else if (response.status === 401) {
      errorMsg = data?.detail || "Authentication required. Please log in again.";
    } else if (response.status === 409) {
      errorMsg = data?.detail || "A task is currently in progress. Please wait and retry.";
    } else if (response.status === 422) {
      errorMsg = data?.detail || "Validation error occurred. Please check input parameters.";
    } else if (response.status === 400) {
      errorMsg = data?.detail || "Bad request.";
    } else if (response.status === 404) {
      errorMsg = data?.detail || "Resource not found or access denied.";
    }
    const err = new Error(errorMsg);
    err.status = response.status;
    err.data = data;
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

export const onboardingApi = {
  getBlueprint: (repoId) =>
    apiRequest(`/repositories/${repoId}/onboarding/blueprint`, {
      method: 'GET',
    }),
  refreshBlueprint: (repoId) =>
    apiRequest(`/repositories/${repoId}/onboarding/blueprint/refresh`, {
      method: 'POST',
    }),
  getProgress: (repoId) =>
    apiRequest(`/repositories/${repoId}/onboarding/progress`, {
      method: 'GET',
    }),
  updateProgress: (repoId, payload) =>
    apiRequest(`/repositories/${repoId}/onboarding/progress`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
};

export const intelligenceApi = {
  getSummary: (repoId) =>
    apiRequest(`/repositories/${repoId}/intelligence/summary`, {
      method: 'GET',
    }),
  getGraph: (repoId, { nodeType = '', search = '', limit = 100 } = {}) => {
    const params = new URLSearchParams();
    if (nodeType) params.append('node_type', nodeType);
    if (search) params.append('search', search);
    if (limit) params.append('limit', limit);
    return apiRequest(`/repositories/${repoId}/intelligence/graph?${params.toString()}`, {
      method: 'GET',
    });
  },
  getArchitectureDiagram: (repoId) =>
    apiRequest(`/repositories/${repoId}/intelligence/architecture-diagram`, {
      method: 'GET',
    }),
  getDependencies: (repoId, ecosystem = '') => {
    const query = ecosystem ? `?ecosystem=${ecosystem}` : '';
    return apiRequest(`/repositories/${repoId}/intelligence/dependencies${query}`, {
      method: 'GET',
    });
  },
  getSymbols: (repoId, { symbolType = '', search = '', limit = 50, offset = 0 } = {}) => {
    const params = new URLSearchParams();
    if (symbolType) params.append('symbol_type', symbolType);
    if (search) params.append('search', search);
    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);
    return apiRequest(`/repositories/${repoId}/intelligence/symbols?${params.toString()}`, {
      method: 'GET',
    });
  },
  triggerIndex: (repoId) =>
    apiRequest(`/repositories/${repoId}/intelligence/index`, {
      method: 'POST',
    }),
};

export const impactApi = {
  getLatestPrImpact: (repoId, prId) =>
    apiRequest(`/repositories/${repoId}/pull-requests/${prId}/impact`, {
      method: 'GET',
    }),
  analyzeImpact: (repoId, payload) =>
    apiRequest(`/repositories/${repoId}/impact/analyze`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getImpactById: (analysisId) =>
    apiRequest(`/impact/${analysisId}`, {
      method: 'GET',
    }),
  getImpactGraph: (analysisId) =>
    apiRequest(`/impact/${analysisId}/graph`, {
      method: 'GET',
    }),
};

export const architectureApi = {
  getLatestAnalysis: (repoId) =>
    apiRequest(`/repositories/${repoId}/architecture/analysis`, {
      method: 'GET',
    }),
  triggerAnalysis: (repoId) =>
    apiRequest(`/repositories/${repoId}/architecture/analyze`, {
      method: 'POST',
    }),
  getRules: (repoId) =>
    apiRequest(`/repositories/${repoId}/architecture/rules`, {
      method: 'GET',
    }),
  createRule: (repoId, payload) =>
    apiRequest(`/repositories/${repoId}/architecture/rules`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateRule: (repoId, ruleId, payload) =>
    apiRequest(`/repositories/${repoId}/architecture/rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteRule: (repoId, ruleId) =>
    apiRequest(`/repositories/${repoId}/architecture/rules/${ruleId}`, {
      method: 'DELETE',
    }),
  resetRules: (repoId) =>
    apiRequest(`/repositories/${repoId}/architecture/rules/reset-defaults`, {
      method: 'POST',
    }),
  getCircularDependencies: (repoId) =>
    apiRequest(`/repositories/${repoId}/architecture/circular`, {
      method: 'GET',
    }),
  getFlows: (repoId) =>
    apiRequest(`/repositories/${repoId}/architecture/flows`, {
      method: 'GET',
    }),
};

export const testingApi = {
  getPrTestScenarios: (repoId, prId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    const endpoint = `/repositories/${repoId}/pull-requests/${prId}/test-intelligence${query ? `?${query}` : ''}`;
    return apiRequest(endpoint, { method: 'GET' });
  },
  triggerTestAnalysis: (repoId, payload) =>
    apiRequest(`/repositories/${repoId}/test-intelligence/analyze`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  generateTestCase: (scenarioId, payload = {}) =>
    apiRequest(`/test-scenarios/${scenarioId}/generate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  executeGeneratedTest: (testId) =>
    apiRequest(`/generated-tests/${testId}/execute`, {
      method: 'POST',
    }),
  getTestDashboard: (prId) =>
    apiRequest(`/test-intelligence/dashboard/${prId}`, {
      method: 'GET',
    }),
};

export const historyApi = {
  getHistoricalPrs: (repoId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/repositories/${repoId}/history/prs${query ? `?${query}` : ''}`, {
      method: 'GET',
    });
  },
  getPreviousChanges: (repoId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/repositories/${repoId}/history/changes${query ? `?${query}` : ''}`, {
      method: 'GET',
    });
  },
  getRecurringIssues: (repoId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/repositories/${repoId}/history/recurring-issues${query ? `?${query}` : ''}`, {
      method: 'GET',
    });
  },
  getAdrs: (repoId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/repositories/${repoId}/history/adrs${query ? `?${query}` : ''}`, {
      method: 'GET',
    });
  },
  getSimilarBugs: (repoId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/repositories/${repoId}/history/similar-bugs${query ? `?${query}` : ''}`, {
      method: 'GET',
    });
  },
  compareChanges: (repoId, payload) =>
    apiRequest(`/repositories/${repoId}/history/compare`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getEvolutionOverview: (repoId) =>
    apiRequest(`/repositories/${repoId}/history/evolution/overview`, {
      method: 'GET',
    }),
  getEvolutionMilestones: (repoId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/repositories/${repoId}/history/evolution/milestones${query ? `?${query}` : ''}`, {
      method: 'GET',
    });
  },
  getModuleEvolution: (repoId, moduleName) =>
    apiRequest(`/repositories/${repoId}/history/modules/${moduleName}/evolution`, {
      method: 'GET',
    }),
  getBugLessons: (repoId, params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/repositories/${repoId}/history/bug-lessons${query ? `?${query}` : ''}`, {
      method: 'GET',
    });
  },
  runImpactAnalysis: (repoId, payload) =>
    apiRequest(`/repositories/${repoId}/history/impact-analysis`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  searchSimilarPrs: (repoId, payload) =>
    apiRequest(`/repositories/${repoId}/history/similar-prs`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  triggerIndex: (repoId, payload = {}) =>
    apiRequest(`/repositories/${repoId}/history/index`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
