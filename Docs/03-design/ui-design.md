# RepoMind 2.0 — UI Design

**Status: Completed**

## Application Shell

A React + Vite + TailwindCSS (v3.4.0) single-page application. The design system uses a premium dark-mode glassmorphism aesthetic with smooth micro-animations.

## Navigation

- **Sidebar navigation:** Includes links to Dashboard, Repositories, My PRs, Security, and Settings.
- Route hierarchy follows the Application Core models.

## Page Hierarchy / Route Structure

| Route | View Component | Purpose |
|---|---|---|
| `/login` | `LoginPage` | Authentication entry point |
| `/` | `DashboardPage` | Overview of active PRs, recent security alerts, and system health |
| `/repositories` | `RepositoriesPage` | List of connected repositories with their sync/index status |
| `/my-prs` | `MyPRsPage` | Developer-focused view of their active PRs awaiting review |
| `/security` | `SecurityBrowserPage` | Organization-wide vulnerability and security findings tracking |
| `/settings` | `SettingsPage` | User profile, GitHub connection, and Org member management |
| `/review/:prId` | `ReviewPage` | Core PR review interface (Findings, Risk, Conflicts, Chat) |

## Reusable / Feature Components — PR Review Page Breakdown

```
ReviewPage
├── TopNav (PR Title, Author, Merge Status)
├── Sidebar (Navigation)
├── MainContent
│   ├── StatsPanel (Risk Score, Conflicts Detected, Files Changed)
│   ├── ChatAssistant (Real-time Gemini AI chat grounded in PR context)
│   ├── FindingsList
│   │   └── FindingCard (Severity badge, category, file:line, evidence, recommendation)
│   └── RiskPanel (Architectural risk & cyclomatic complexity)
```

## State Management

| State Type | Used For | Tool |
|---|---|---|
| Server state | Repositories, PRs, findings, session auth | `TanStack Query` |
| Client state | UI toggles (expanded finding, chat input) | React `useState` |
| Route state | Current page, active PR id | `react-router-dom` |

## Design System

The application uses a strict set of Tailwind utility tokens to achieve its look:
- **Backgrounds:** `#09090b` (Main), `#18181b` (Cards/Panels)
- **Glassmorphism:** `bg-white/5` with `backdrop-blur-xl` and `border-white/10`
- **Accents:** Indigo and Violet gradients for primary actions and AI elements
- **Typography:** Inter/sans-serif with crisp contrast
- **Micro-animations:** Hover transitions (`transition-all duration-200`) and entry animations.
