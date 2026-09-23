import re

file_path = 'frontend/src/lib/api.js'
with open(file_path, 'r') as f:
    content = f.read()

events_api = """
  // Phase 18: Events API
  getPullRequestEvents: async (pullRequestId) => {
    const res = await api.get(`/api/github/pull-requests/${pullRequestId}/events`);
    return res.data;
  },
"""

content = content.replace("  getPullRequest: async (pullRequestId) => {\n    const res = await api.get(`/api/github/pull-requests/${pullRequestId}`);\n    return res.data;\n  },", "  getPullRequest: async (pullRequestId) => {\n    const res = await api.get(`/api/github/pull-requests/${pullRequestId}`);\n    return res.data;\n  }," + events_api)

with open(file_path, 'w') as f:
    f.write(content)
