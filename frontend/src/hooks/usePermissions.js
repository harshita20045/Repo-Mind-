import { useMemo } from 'react';

// Permission strings matching backend/app/auth/permissions.py
export const Permissions = {
  // Organization
  ORG_READ: 'organization.read',
  ORG_UPDATE: 'organization.update',
  
  // Members
  MEMBERS_READ: 'members.read',
  MEMBERS_INVITE: 'members.invite',
  MEMBERS_UPDATE: 'members.update',
  MEMBERS_REMOVE: 'members.remove',
  
  // Projects
  PROJECTS_READ: 'projects.read',
  PROJECTS_CREATE: 'projects.create',
  PROJECTS_UPDATE: 'projects.update',
  PROJECTS_DELETE: 'projects.delete',
  
  // Repositories
  REPOS_READ: 'repositories.read',
  REPOS_CONNECT: 'repositories.connect',
  REPOS_UPDATE: 'repositories.update',
  REPOS_DELETE: 'repositories.delete',
  REPOS_INDEX: 'repositories.index',
  
  // PRs
  PRS_READ: 'prs.read',
  PRS_REVIEW: 'prs.review',
  PRS_APPROVE: 'prs.approve',
  PRS_REQUEST_CHANGES: 'prs.request_changes',
  
  // Findings
  FINDINGS_READ: 'findings.read',
  FINDINGS_DISMISS: 'findings.dismiss',
  FINDINGS_FEEDBACK: 'findings.feedback',
  
  // Reviews
  REVIEWS_RUN: 'reviews.run',
  REVIEWS_READ: 'reviews.read',
  
  // Analytics & Security & Audit
  ANALYTICS_READ: 'analytics.read',
  SECURITY_READ: 'security.read',
  AUDIT_READ: 'audit.read',
  POLICIES_READ: 'policies.read',
  POLICIES_UPDATE: 'policies.update',
  
  // Chat
  CHAT_USE: 'chat.use',
};

// Map backend role enum to capabilities (matching the python backend).
// Notice that we handle legacy roles like tech_lead as LEAD, 
// but we map based on the backend role strings directly.
const ROLE_PERMISSIONS = {
  developer: [
    Permissions.ORG_READ, Permissions.MEMBERS_READ, Permissions.PROJECTS_READ,
    Permissions.REPOS_READ, Permissions.PRS_READ, Permissions.FINDINGS_READ,
    Permissions.REVIEWS_READ, Permissions.ANALYTICS_READ, Permissions.SECURITY_READ,
    Permissions.REVIEWS_RUN, Permissions.FINDINGS_FEEDBACK, Permissions.CHAT_USE,
    Permissions.POLICIES_READ
  ],
  reviewer: [
    // Includes developer
    Permissions.ORG_READ, Permissions.MEMBERS_READ, Permissions.PROJECTS_READ,
    Permissions.REPOS_READ, Permissions.PRS_READ, Permissions.FINDINGS_READ,
    Permissions.REVIEWS_READ, Permissions.ANALYTICS_READ, Permissions.SECURITY_READ,
    Permissions.REVIEWS_RUN, Permissions.FINDINGS_FEEDBACK, Permissions.CHAT_USE,
    Permissions.POLICIES_READ,
    // Plus reviewer specific
    Permissions.PRS_REVIEW, Permissions.PRS_REQUEST_CHANGES, Permissions.FINDINGS_DISMISS
  ],
  tech_lead: [
    // Includes reviewer
    Permissions.ORG_READ, Permissions.MEMBERS_READ, Permissions.PROJECTS_READ,
    Permissions.REPOS_READ, Permissions.PRS_READ, Permissions.FINDINGS_READ,
    Permissions.REVIEWS_READ, Permissions.ANALYTICS_READ, Permissions.SECURITY_READ,
    Permissions.REVIEWS_RUN, Permissions.FINDINGS_FEEDBACK, Permissions.CHAT_USE,
    Permissions.POLICIES_READ, Permissions.PRS_REVIEW, Permissions.PRS_REQUEST_CHANGES, 
    Permissions.FINDINGS_DISMISS,
    // Plus tech_lead specific
    Permissions.PRS_APPROVE, Permissions.REPOS_INDEX
  ],
  team_lead: [
    // Legacy alias to tech_lead
    Permissions.ORG_READ, Permissions.MEMBERS_READ, Permissions.PROJECTS_READ,
    Permissions.REPOS_READ, Permissions.PRS_READ, Permissions.FINDINGS_READ,
    Permissions.REVIEWS_READ, Permissions.ANALYTICS_READ, Permissions.SECURITY_READ,
    Permissions.REVIEWS_RUN, Permissions.FINDINGS_FEEDBACK, Permissions.CHAT_USE,
    Permissions.POLICIES_READ, Permissions.PRS_REVIEW, Permissions.PRS_REQUEST_CHANGES, 
    Permissions.FINDINGS_DISMISS, Permissions.PRS_APPROVE, Permissions.REPOS_INDEX
  ],
  org_admin: [
    // Eng manager permissions
    Permissions.ORG_READ, Permissions.MEMBERS_READ, Permissions.PROJECTS_READ,
    Permissions.REPOS_READ, Permissions.PRS_READ, Permissions.FINDINGS_READ,
    Permissions.REVIEWS_READ, Permissions.ANALYTICS_READ, Permissions.SECURITY_READ,
    Permissions.REVIEWS_RUN, Permissions.FINDINGS_FEEDBACK, Permissions.CHAT_USE,
    Permissions.POLICIES_READ, Permissions.PRS_REVIEW, Permissions.PRS_REQUEST_CHANGES, 
    Permissions.FINDINGS_DISMISS, Permissions.PRS_APPROVE, Permissions.REPOS_INDEX,
    Permissions.PROJECTS_CREATE, Permissions.PROJECTS_UPDATE, Permissions.AUDIT_READ,
    // Plus org_admin specific
    Permissions.ORG_UPDATE, Permissions.MEMBERS_INVITE, Permissions.MEMBERS_UPDATE,
    Permissions.MEMBERS_REMOVE, Permissions.PROJECTS_DELETE, Permissions.REPOS_CONNECT,
    Permissions.REPOS_UPDATE, Permissions.REPOS_DELETE, Permissions.POLICIES_UPDATE
  ]
};

// Fallback for roles that are outside the target 4 roles but might exist in DB
// For example, if someone has security_reviewer or org_owner, we map them to an equivalent
// capability set for safety, though the UI will only treat them as their base capabilities.
ROLE_PERMISSIONS.security_reviewer = [
  ...ROLE_PERMISSIONS.reviewer, 
  Permissions.PRS_APPROVE,
];
ROLE_PERMISSIONS.eng_manager = [
  ...ROLE_PERMISSIONS.tech_lead,
  Permissions.PROJECTS_CREATE, Permissions.PROJECTS_UPDATE, Permissions.AUDIT_READ
];
ROLE_PERMISSIONS.org_owner = [
  ...ROLE_PERMISSIONS.org_admin
];
ROLE_PERMISSIONS.read_only = [
    Permissions.ORG_READ, Permissions.MEMBERS_READ, Permissions.PROJECTS_READ,
    Permissions.REPOS_READ, Permissions.PRS_READ, Permissions.FINDINGS_READ,
    Permissions.REVIEWS_READ, Permissions.ANALYTICS_READ, Permissions.SECURITY_READ,
    Permissions.POLICIES_READ
];

/**
 * usePermissions hook
 * 
 * @param {Array} memberships - user memberships from AuthContext/props
 * @param {number|string} [orgId] - optional orgId to scope permission check (future proofing)
 */
export function usePermissions(memberships = [], orgId = null) {
  return useMemo(() => {
    // Determine active role(s). If orgId is provided, filter for that org.
    // Otherwise, we take the highest privilege role or just all roles.
    // For simplicity in a single-org view (or global view), we merge all granted permissions.
    const activeMemberships = orgId 
      ? memberships.filter(m => m.organization_id == orgId)
      : memberships;

    const grantedPermissions = new Set();
    const activeRoles = new Set();

    activeMemberships.forEach(m => {
      const role = m.role?.toLowerCase() || 'read_only';
      activeRoles.add(role);
      const perms = ROLE_PERMISSIONS[role] || [];
      perms.forEach(p => grantedPermissions.add(p));
    });

    const can = (permission) => grantedPermissions.has(permission);

    // Checks if user has a specific backend role (exact match).
    // Mostly you should use `can(permission)`.
    const hasRole = (role) => activeRoles.has(role.toLowerCase());

    return {
      can,
      hasRole,
      // For convenience to check the 4 target roles, though `can()` is preferred
      isOrgAdmin: hasRole('org_admin') || hasRole('org_owner'),
      isLead: hasRole('tech_lead') || hasRole('team_lead') || hasRole('eng_manager'),
      isReviewer: hasRole('reviewer') || hasRole('security_reviewer'),
      isDeveloper: hasRole('developer') || activeRoles.size === 0,
    };
  }, [memberships, orgId]);
}
