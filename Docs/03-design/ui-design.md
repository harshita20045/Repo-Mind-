# RepoMind — UI Design

**Status: Confirmed** (routes and structure per the Implementation Blueprint, Part 9)

## Application Shell

A React + TypeScript + Tailwind CSS single-page application. There is no separate admin dashboard shell — settings and administrative actions (connecting a GitHub repository, managing members) live within the same navigation as everything else, gated by role.

## Navigation

- **Top navigation / sidebar:** organization context, links to Dashboard, Projects, Evaluation, Settings.
- Route hierarchy follows the Organization → Project → Repository → Pull Request data model.

## Page Hierarchy / Route Structure

| Route | Purpose | Key Components | Loading / Empty / Error States |
|---|---|---|---|
| `/login` | Authentication entry point | `LoginForm` | Error state on bad credentials |
| `/dashboard` | Organization overview | `ProjectList`, `RecentActivity` | Empty state for new organizations |
| `/projects` | List projects | `ProjectCard[]` | Empty state, create prompt (admin only) |
| `/projects/:id` | Repositories within a project | `RepositoryCard[]` | — |
| `/projects/:pid/repositories/:rid` | Repository overview: rules, PR list (tabs) | `RepoHeader`, `RulesList`, `PRList` | Loading spinner during indexing |
| `/repositories/:rid/pull-requests/:prid` | Core PR review page | `PRHeader`, `PRMetadata`, `FindingsSummary`, `FindingList` → `FindingCard`, `LinterResults`, `RiskPanel`, `ReviewTimeline` | Loading state during the async review job; error state on job failure |
| `/evaluation` | Comparison table | `EvaluationTable`, `RunEvaluationButton` | Empty state before the first run |
| `/settings` | Profile, org, GitHub connection | `ProfileForm`, `GitHubConnectionPanel`, `MemberList` | — |

**Note on route naming:** the source materials list both `/pull-requests/:pullRequestId` / `/pull-requests/:pullRequestId/review` (in the general project structure) and the more specific `/repositories/:rid/pull-requests/:prid` (in the Implementation Blueprint's confirmed 9-page frontend). Per the "prefer the latest explicit decision" rule, the confirmed route is `/repositories/:rid/pull-requests/:prid`, matching the Organization → Project → Repository → PR hierarchy actually modeled in the database.

**Deferred route (Future, P2):** `/team-analytics` — team/repository trend views only, no individual ranking, built only on explicit request. Not part of the current 9 confirmed pages' functionality beyond being reserved as a route.

No route exists for individual developer performance/ranking pages — this is a deliberate omission, not an oversight (see `01-project/requirements.md`, NFR-010).

## Reusable / Feature Components — PR Review Page Breakdown

```
PullRequestPage
├── PRHeader (title, author, status)
├── PRMetadata (files, additions/deletions)
├── RiskPanel (ML cycle-time + delay prediction)
├── FindingsSummary (counts by severity)
├── FindingList
│   └── FindingCard (severity, category, file:line, evidence, recommendation, accept/reject buttons)
├── LinterResults (raw static-analysis output, collapsed by default)
└── ReviewTimeline (history of review_runs for this PR)
```

## State Management

| State Type | Used For | Tool |
|---|---|---|
| Server state | Projects, repositories, PRs, findings | React Query (or equivalent fetch+cache) — no Redux |
| Client state | UI toggles (expanded finding, filter selection) | Local component state |
| URL state | Current project/repository/PR id, active tab | Route params |
| Form state | Login, GitHub connection, feedback reason | Local form state |

No global state library is used — nothing in the confirmed scope requires cross-cutting client state beyond what the router and query cache already provide.

## UI States

- **Loading:** shown during repository indexing and during an in-progress async review job (the review job's status is polled from `GET /review-runs/{id}`).
- **Empty:** shown for new organizations with no projects, projects with no repositories, and the Evaluation page before the first run.
- **Error:** shown on bad login credentials and on review job failure (see the error-handling matrix in `06-testing/testing-strategy.md`), with a retry action where applicable.

## Responsive Behavior

Not specified in detail in the source materials beyond the choice of Tailwind CSS, which supports responsive utility classes. Specific breakpoint behavior is left to implementation-time design decisions — **not specified as a confirmed requirement beyond "use Tailwind."**
