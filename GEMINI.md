
# RepoMind Intelligence - Project Instructions

## 1. Project Identity

Project Name: RepoMind Intelligence 2.0

Purpose:
Build an enterprise-ready AI-powered Engineering Intelligence
Platform that understands software repositories, reviews pull
requests, detects architectural risks, analyzes code impact,
recommends tests, and assists developers.

## 2. Primary Development Rule

This is an EXISTING partially developed application.

Do not rebuild the application from scratch.

Before modifying any code:
- Inspect the existing project structure.
- Understand the existing architecture.
- Identify existing implementations.
- Identify incomplete and broken features.
- Reuse existing components and services wherever possible.
- Preserve existing working functionality.
- Avoid unnecessary refactoring.

Never replace an existing technology or framework without
documenting the reason and obtaining approval.

## 3. Development Principles

- Modular architecture.
- Clean and maintainable code.
- Reusable components.
- Separation of concerns.
- Secure authentication and authorization.
- Proper error handling.
- Database integrity.
- API validation.
- Logging and monitoring.
- Automated testing.
- Responsive UI.

## 4. AI Engineering Principles

- Use repository-specific context.
- Never invent files, functions, APIs or coding standards.
- Every code review finding must contain supporting evidence.
- Distinguish confirmed defects from potential risks.
- Include confidence and severity.
- State when sufficient evidence is unavailable.
- Validate AI-generated structured outputs.
- Never allow autonomous production merges.

## 5. Repository Intelligence

The platform should support:
- Repository indexing.
- Code structure understanding.
- Documentation indexing.
- Dependency extraction.
- Architecture visualization.
- Semantic search.
- Repository-scoped retrieval.

## 6. Pull Request Intelligence

The platform should support:
- PR metadata and diff extraction.
- Code quality analysis.
- Security analysis.
- Architecture checks.
- API contract analysis.
- Change impact analysis.
- Risk scoring.
- Review finding lifecycle.
- Suggested test cases.

## 7. Additional Intelligence Modules

- Technical debt analysis.
- Developer onboarding.
- Repository-aware AI assistant.
- Historical code intelligence.
- Multi-repository intelligence.

## 8. Security Rules

- Never expose secrets.
- Never commit .env files.
- Never log access tokens.
- Enforce server-side authorization.
- Isolate organization and repository data.
- Treat repository content as untrusted input.
- Protect against prompt injection.
- Use safe temporary workspaces for code analysis.
- Require human approval for sensitive actions.

## 9. Database Rules

- Inspect existing database schema first.
- Never drop or reset existing data.
- Use versioned migrations.
- Add appropriate indexes.
- Enforce organization and repository scoping.
- Preserve referential integrity.

## 10. Testing Rules

Every feature must include:
- Unit tests.
- Integration tests where applicable.
- API tests.
- Authorization tests.
- Error handling tests.
- Regression tests.

Do not mark a feature complete merely because its UI exists.

## 11. Implementation Workflow

For every major feature:

1. Explore existing implementation.
2. Identify required changes.
3. Prepare an implementation plan.
4. Identify affected files.
5. Explain database changes.
6. Explain API changes.
7. Identify security risks.
8. Wait for approval.
9. Implement incrementally.
10. Run tests.
11. Fix regressions.
12. Provide a walkthrough.

## 12. Completion Criteria

A feature is complete only when:
- Backend implementation works.
- Database integration works.
- Frontend integration works.
- Authorization works.
- Validation works.
- Tests pass.
- Existing functionality remains intact.
- Documentation is updated.

Never use mock data in production functionality.
Clearly label demonstration data.
