"""
Multi-Source Context Retriever for RepoMind AI Assistant.

Integrates 7 context sources:
1. Repository source code & AST symbols (CodeGraphNode, DocumentChunk)
2. Documentation & blueprint (RepositoryBlueprint, RepositoryScanSummary, DocumentChunk)
3. Architecture rules & violations (ArchitectureRule, ArchitectureViolation)
4. Dependency graph & call chains (CodeGraphNode, CodeGraphEdge)
5. Pull request diffs (PullRequest, PullRequestFile)
6. Review findings (ReviewRun, Finding, FindingEvidence)
7. Historical decisions & test scenarios (HumanDecision, TestScenario)
"""
import logging
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from backend.app.chat.classifier import ExtractedEntities, QueryIntent
from backend.app.intelligence.models import (
    CodeGraphNode,
    CodeGraphEdge,
    RepositoryScanSummary,
    PackageDependency,
)
from backend.app.onboarding.models import RepositoryBlueprint
from backend.app.architecture.models import ArchitectureRule, ArchitectureAnalysis, ArchitectureViolation
from backend.app.github.models import PullRequest, PullRequestFile
from backend.app.review.models import ReviewRun, Finding, HumanDecision
from backend.app.testing.models import TestScenario
from backend.app.history.models import (
    ArchitectureDecisionRecord,
    HistoricalCommitRecord,
    RecurringIssueHotspot,
    HistoricalEvolutionMilestone,
    HistoricalBugLesson,
)
from backend.app.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)


class MultiSourceContextRetriever:
    """
    Orchestrates multi-source repository context retrieval based on classified intent and entities.
    """

    def __init__(self, db: Session):
        self.db = db
        self.rag_retriever = RAGRetriever(db=db)

    def retrieve(
        self,
        repository_id: int,
        query: str,
        entities: ExtractedEntities,
        top_k: int = 5,
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Retrieves grounded evidence from relevant sources.
        Returns:
            evidence_text: formatted string of evidence blocks.
            sources: list of source citation dicts.
            has_grounded_evidence: boolean indicating whether meaningful evidence was found.
        """
        evidence_sections: List[str] = []
        sources: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # 1. ARCHITECTURE BLUEPRINT & SCAN SUMMARY (Documentation source)
        # -------------------------------------------------------------
        blueprint = (
            self.db.query(RepositoryBlueprint)
            .filter(RepositoryBlueprint.repository_id == repository_id)
            .first()
        )
        scan_summary = (
            self.db.query(RepositoryScanSummary)
            .filter(RepositoryScanSummary.repository_id == repository_id)
            .first()
        )

        if entities.intent in (
            QueryIntent.MODULE_EXPLANATION,
            QueryIntent.AUTH_FLOW,
            QueryIntent.ENDPOINT_LIFECYCLE,
            QueryIntent.GENERAL_CODE_SEARCH,
        ):
            doc_lines = []
            if scan_summary and scan_summary.architecture_summary:
                doc_lines.append(f"Architecture Summary:\n{scan_summary.architecture_summary}")
                if scan_summary.entry_points:
                    doc_lines.append(f"Entry Points: {scan_summary.entry_points}")
                sources.append({
                    "type": "documentation",
                    "path": "RepositoryScanSummary",
                    "symbol": "architecture_summary",
                    "summary": "Repository scan overview and entry points",
                })

            if blueprint:
                if entities.intent == QueryIntent.AUTH_FLOW and blueprint.application_flows:
                    auth_flow = (
                        blueprint.application_flows.get("auth_flow")
                        or blueprint.application_flows.get("auth")
                        or blueprint.application_flows.get("authentication")
                    )
                    if auth_flow:
                        doc_lines.append(f"Authentication Flow:\n{auth_flow}")
                        sources.append({
                            "type": "documentation",
                            "path": "RepositoryBlueprint",
                            "symbol": "application_flows.auth",
                            "summary": "Documented authentication execution flow",
                        })
                elif entities.intent == QueryIntent.MODULE_EXPLANATION and blueprint.application_flows:
                    if isinstance(blueprint.application_flows, list):
                        flows_text = "\n".join([f"- {f.get('title')}: {f.get('description')} ({', '.join(f.get('files', []))})" for f in blueprint.application_flows[:4]])
                    elif isinstance(blueprint.application_flows, dict):
                        flows_text = "\n".join([f"- {k}: {v}" for k, v in list(blueprint.application_flows.items())[:4]])
                    else:
                        flows_text = str(blueprint.application_flows)
                    doc_lines.append(f"Key Application Flows:\n{flows_text}")
                    sources.append({
                        "type": "documentation",
                        "path": "RepositoryBlueprint",
                        "symbol": "application_flows",
                        "summary": "Key application flows and module responsibilities",
                    })

                if blueprint.summary and entities.intent == QueryIntent.MODULE_EXPLANATION:
                    doc_lines.append(f"Blueprint Overview:\n{blueprint.summary}")
                    sources.append({
                        "type": "documentation",
                        "path": "RepositoryBlueprint",
                        "symbol": "summary",
                        "summary": "High-level architectural summary",
                    })
                    sources.append({
                        "type": "documentation",
                        "path": "RepositoryBlueprint",
                        "symbol": "architecture_overview",
                        "summary": "High-level architecture overview",
                    })

            if doc_lines:
                evidence_sections.append("=== REPOSITORY ARCHITECTURE & BLUEPRINT ===\n" + "\n\n".join(doc_lines))

        # -------------------------------------------------------------
        # 2. ARCHITECTURE RULES & VIOLATIONS (Architecture source)
        # -------------------------------------------------------------
        rules = (
            self.db.query(ArchitectureRule)
            .filter(
                ArchitectureRule.repository_id == repository_id,
                ArchitectureRule.is_enabled == True,
            )
            .all()
        )
        if rules and entities.intent in (
            QueryIntent.MODULE_EXPLANATION,
            QueryIntent.AUTH_FLOW,
            QueryIntent.PR_REVIEW_RATIONALE,
            QueryIntent.DB_ACCESS,
            QueryIntent.GENERAL_CODE_SEARCH,
        ):
            rule_texts = []
            for r in rules[:8]:
                rule_texts.append(
                    f"Rule [{r.rule_code}] ({r.severity.upper()}): {r.name}\n"
                    f"Type: {r.rule_type} | Source: {r.source_pattern or r.source_layer} -> Target: {r.target_pattern or r.target_layer}\n"
                    f"Description: {r.description}"
                )
                sources.append({
                    "type": "architecture_rule",
                    "path": f"Rule:{r.rule_code}",
                    "symbol": r.rule_code,
                    "summary": f"{r.name} ({r.severity})",
                })
            evidence_sections.append("=== ARCHITECTURE RULES & CONSTRAINTS ===\n" + "\n\n".join(rule_texts))

        # -------------------------------------------------------------
        # 3. CODE GRAPH AST NODES (Source code AST & symbol definitions)
        # -------------------------------------------------------------
        node_filters = []
        if entities.symbols:
            for s in entities.symbols:
                node_filters.append(CodeGraphNode.name.ilike(f"%{s}%"))
        if entities.files:
            for f in entities.files:
                node_filters.append(CodeGraphNode.file_path.ilike(f"%{f}%"))
        if entities.endpoints:
            for ep in entities.endpoints:
                node_filters.append(CodeGraphNode.name.ilike(f"%{ep}%"))
                node_filters.append(CodeGraphNode.node_key.ilike(f"%{ep}%"))

        matched_nodes: List[CodeGraphNode] = []
        if node_filters:
            matched_nodes = (
                self.db.query(CodeGraphNode)
                .filter(
                    CodeGraphNode.repository_id == repository_id,
                    or_(*node_filters),
                )
                .limit(10)
                .all()
            )
        elif entities.intent in (QueryIntent.API_IMPLEMENTATION, QueryIntent.ENDPOINT_LIFECYCLE):
            matched_nodes = (
                self.db.query(CodeGraphNode)
                .filter(
                    CodeGraphNode.repository_id == repository_id,
                    CodeGraphNode.node_type.in_(["api_endpoint", "service"]),
                )
                .limit(10)
                .all()
            )
        elif entities.intent == QueryIntent.DB_ACCESS:
            matched_nodes = (
                self.db.query(CodeGraphNode)
                .filter(
                    CodeGraphNode.repository_id == repository_id,
                    CodeGraphNode.node_type.in_(["db_model", "service"]),
                )
                .limit(10)
                .all()
            )

        if matched_nodes:
            node_texts = []
            for n in matched_nodes:
                line_info = f"lines {n.start_line}-{n.end_line}" if n.start_line and n.end_line else "unknown line"
                node_texts.append(
                    f"Symbol: {n.name} [{n.node_type.upper()}]\n"
                    f"File: {n.file_path} ({line_info})\n"
                    f"Key: {n.node_key}\n"
                    f"Metadata: {n.metadata_json or {}}"
                )
                sources.append({
                    "type": "code_symbol",
                    "path": n.file_path,
                    "symbol": n.name,
                    "summary": f"{n.node_type} defined at {line_info}",
                    "line_range": [n.start_line, n.end_line] if n.start_line else None,
                })
            evidence_sections.append("=== AST SYMBOLS & DEFINITIONS ===\n" + "\n\n".join(node_texts))

        # -------------------------------------------------------------
        # 4. DEPENDENCY GRAPH & CALL CHAINS (Dependency Graph source)
        # -------------------------------------------------------------
        if matched_nodes or entities.intent in (
            QueryIntent.DEPENDENCY_GRAPH,
            QueryIntent.ENDPOINT_LIFECYCLE,
            QueryIntent.DB_ACCESS,
        ):
            target_ids = [n.id for n in matched_nodes]
            edges = []
            if target_ids:
                # Incoming edges (who calls or depends on these nodes)
                incoming_edges = (
                    self.db.query(CodeGraphEdge)
                    .filter(
                        CodeGraphEdge.repository_id == repository_id,
                        CodeGraphEdge.target_node_id.in_(target_ids),
                    )
                    .limit(10)
                    .all()
                )
                # Outgoing edges (who these nodes call or interact with)
                outgoing_edges = (
                    self.db.query(CodeGraphEdge)
                    .filter(
                        CodeGraphEdge.repository_id == repository_id,
                        CodeGraphEdge.source_node_id.in_(target_ids),
                    )
                    .limit(10)
                    .all()
                )
                edges = incoming_edges + outgoing_edges
            elif entities.intent == QueryIntent.DB_ACCESS:
                # Find edges targeting db_models or interacting with DB
                edges = (
                    self.db.query(CodeGraphEdge)
                    .join(CodeGraphNode, CodeGraphEdge.target_node_id == CodeGraphNode.id)
                    .filter(
                        CodeGraphEdge.repository_id == repository_id,
                        CodeGraphNode.node_type == "db_model",
                    )
                    .limit(10)
                    .all()
                )

            if edges:
                edge_texts = []
                for e in edges[:12]:
                    src = e.source_node
                    tgt = e.target_node
                    edge_texts.append(
                        f"Relationship: [{src.node_type}] {src.name} ({src.file_path}) "
                        f"--[{e.relation_type.upper()}]--> "
                        f"[{tgt.node_type}] {tgt.name} ({tgt.file_path})"
                    )
                    sources.append({
                        "type": "dependency_graph",
                        "path": src.file_path,
                        "symbol": f"{src.name} -> {tgt.name}",
                        "summary": f"{e.relation_type} relationship",
                    })
                evidence_sections.append("=== DEPENDENCY GRAPH & CALL RELATIONSHIPS ===\n" + "\n".join(edge_texts))

        # -------------------------------------------------------------
        # 5. PULL REQUEST DIFFS & METADATA (PR source)
        # -------------------------------------------------------------
        pr = None
        if entities.pr_id:
            pr = (
                self.db.query(PullRequest)
                .filter(
                    PullRequest.repository_id == repository_id,
                    or_(
                        PullRequest.id == entities.pr_id,
                        PullRequest.github_number == entities.pr_id,
                    ),
                )
                .first()
            )
        
        if pr:
            pr_info = [
                f"PR #{pr.github_number}: {pr.title}",
                f"Author: {pr.github_author_login} | State: {pr.state}",
                f"Branch: {pr.source_branch} -> {pr.target_branch} (Head SHA: {pr.head_sha})",
            ]
            pr_files = (
                self.db.query(PullRequestFile)
                .filter(PullRequestFile.pull_request_id == pr.id)
                .limit(8)
                .all()
            )
            if pr_files:
                pr_info.append("Changed Files in PR:")
                for pf in pr_files:
                    file_name = getattr(pf, "file_path", None) or getattr(pf, "filename", "unknown")
                    patch_content = getattr(pf, "patch_data", None) or getattr(pf, "patch", None)
                    pr_info.append(f"- {file_name} ({pf.status}: +{pf.additions}/-{pf.deletions})")
                    if patch_content and len(patch_content) < 400:
                        pr_info.append(f"  Patch snippet:\n{patch_content[:300]}")
                    sources.append({
                        "type": "pr_diff",
                        "path": file_name,
                        "symbol": f"PR#{pr.github_number}",
                        "summary": f"Diff: +{pf.additions}/-{pf.deletions}",
                    })
            evidence_sections.append("=== PULL REQUEST CONTEXT & DIFF ===\n" + "\n".join(pr_info))

        # -------------------------------------------------------------
        # 6. REVIEW FINDINGS & HUMAN DECISIONS (Review Findings source)
        # -------------------------------------------------------------
        if pr or entities.intent == QueryIntent.PR_REVIEW_RATIONALE:
            findings_query = self.db.query(Finding).join(ReviewRun)
            if pr:
                findings_query = findings_query.filter(ReviewRun.pull_request_id == pr.id)
            else:
                findings_query = (
                    findings_query.join(PullRequest)
                    .filter(PullRequest.repository_id == repository_id)
                )

            findings = (
                findings_query.order_by(desc(Finding.id))
                .limit(6)
                .all()
            )
            if findings:
                finding_texts = []
                for f in findings:
                    finding_texts.append(
                        f"Finding [{f.severity.upper()} - {f.type}]: {f.title}\n"
                        f"File: {f.file or 'unknown'}:{f.line or '?'}\n"
                        f"Explanation: {f.explanation}\n"
                        f"Rule Source: {f.rule_source or 'standard'}\n"
                        f"Status: {f.status} (Evidence: {f.evidence_status})"
                    )
                    sources.append({
                        "type": "review_finding",
                        "path": f.file or "PR Review",
                        "symbol": f.title,
                        "summary": f"{f.severity.upper()} {f.type}: {f.explanation[:120]}",
                    })
                evidence_sections.append("=== REVIEW FINDINGS & AUDIT FLAGS ===\n" + "\n\n".join(finding_texts))

            # Check human decisions
            if pr:
                decisions = (
                    self.db.query(HumanDecision)
                    .join(ReviewRun)
                    .filter(ReviewRun.pull_request_id == pr.id)
                    .all()
                )
                if decisions:
                    dec_texts = [f"Decision by {d.reviewer}: {d.decision} (Reason: {d.reason})" for d in decisions]
                    evidence_sections.append("=== HISTORICAL HUMAN REVIEW DECISIONS ===\n" + "\n".join(dec_texts))
                    sources.append({
                        "type": "historical_decision",
                        "path": f"PR#{pr.github_number}",
                        "symbol": "HumanDecision",
                        "summary": f"{len(decisions)} human review decisions recorded",
                    })

        # -------------------------------------------------------------
        # 7. TEST SCENARIOS & COVERAGE (Testing Intelligence source)
        # -------------------------------------------------------------
        test_scenarios_query = self.db.query(TestScenario).filter(TestScenario.repository_id == repository_id)
        if entities.symbols:
            test_scenarios_query = test_scenarios_query.filter(
                or_(*[TestScenario.target_symbol.ilike(f"%{s}%") for s in entities.symbols])
            )
        elif entities.files:
            test_scenarios_query = test_scenarios_query.filter(
                or_(*[TestScenario.target_file.ilike(f"%{f}%") for f in entities.files])
            )

        test_scenarios = test_scenarios_query.limit(6).all()
        if test_scenarios or entities.intent == QueryIntent.TEST_COVERAGE:
            if not test_scenarios:
                # Fallback to general test scenarios for repo
                test_scenarios = (
                    self.db.query(TestScenario)
                    .filter(TestScenario.repository_id == repository_id)
                    .limit(5)
                    .all()
                )

            if test_scenarios:
                test_texts = []
                for ts in test_scenarios:
                    gap_label = "COVERAGE GAP" if ts.coverage_gap else "COVERED"
                    test_texts.append(
                        f"Test Scenario [{ts.category.upper()}] - {ts.title} ({gap_label})\n"
                        f"Target: {ts.target_symbol} in {ts.target_file}\n"
                        f"Existing Test File: {ts.existing_test_file or 'None'}\n"
                        f"Description: {ts.description}"
                    )
                    sources.append({
                        "type": "test_scenario",
                        "path": ts.target_file,
                        "symbol": ts.target_symbol,
                        "summary": f"[{ts.category}] {ts.title} (Gap: {ts.coverage_gap})",
                    })
                evidence_sections.append("=== AI TEST INTELLIGENCE & SCENARIOS ===\n" + "\n\n".join(test_texts))

        # -------------------------------------------------------------
        # 7b. HISTORICAL DECISIONS & RECURRING BUGS (ADRs, Commits, Hotspots)
        # -------------------------------------------------------------
        if entities.intent in (QueryIntent.HISTORICAL_DECISION, QueryIntent.MODULE_EXPLANATION, QueryIntent.GENERAL_CODE_SEARCH):
            adr_query = self.db.query(ArchitectureDecisionRecord).filter(
                ArchitectureDecisionRecord.repository_id == repository_id
            )
            # Check if query matches ADR titles, decisions, or affected modules
            words = [w for w in query.lower().split() if len(w) > 3 and w not in ("what", "which", "when", "where", "this", "that", "does", "explain", "about")]
            if words:
                conditions = []
                for w in words[:4]:
                    conditions.append(ArchitectureDecisionRecord.title.ilike(f"%{w}%"))
                    conditions.append(ArchitectureDecisionRecord.decision.ilike(f"%{w}%"))
                    conditions.append(ArchitectureDecisionRecord.context.ilike(f"%{w}%"))
                matching_adrs = adr_query.filter(or_(*conditions)).limit(4).all()
            else:
                matching_adrs = adr_query.limit(3).all()

            if not matching_adrs and entities.intent == QueryIntent.HISTORICAL_DECISION:
                matching_adrs = adr_query.limit(4).all()

            if matching_adrs:
                adr_texts = []
                for adr in matching_adrs:
                    adr_texts.append(
                        f"ADR [{adr.adr_number}] {adr.title} ({adr.status})\n"
                        f"Context: {adr.context}\n"
                        f"Decision: {adr.decision}\n"
                        f"Reason: {adr.reason}\n"
                        f"Consequences: {adr.consequences}"
                    )
                    sources.append({
                        "type": "architecture_decision_record",
                        "path": adr.file_source or f"ADR/{adr.adr_number}",
                        "symbol": adr.adr_number,
                        "summary": f"{adr.title}: {adr.decision[:120]}",
                    })
                evidence_sections.append("=== ARCHITECTURE DECISION RECORDS (ADRs) ===\n" + "\n\n".join(adr_texts))

            # Historical bugfix commits or commits matching keywords
            commit_query = self.db.query(HistoricalCommitRecord).filter(
                HistoricalCommitRecord.repository_id == repository_id
            )
            if "bug" in query.lower() or "issue" in query.lower() or "regression" in query.lower() or "fix" in query.lower():
                commit_query = commit_query.filter(HistoricalCommitRecord.is_bugfix == True)
            if words:
                c_conditions = []
                for w in words[:3]:
                    c_conditions.append(HistoricalCommitRecord.message.ilike(f"%{w}%"))
                    c_conditions.append(HistoricalCommitRecord.original_decision_rationale.ilike(f"%{w}%"))
                matching_commits = commit_query.filter(or_(*c_conditions)).limit(4).all()
            else:
                matching_commits = commit_query.order_by(desc(HistoricalCommitRecord.committed_at)).limit(3).all()

            if not matching_commits and entities.intent == QueryIntent.HISTORICAL_DECISION:
                matching_commits = commit_query.order_by(desc(HistoricalCommitRecord.committed_at)).limit(4).all()

            if matching_commits:
                commit_texts = []
                for c in matching_commits:
                    date_str = c.committed_at.strftime("%Y-%m-%d") if c.committed_at else "past"
                    commit_texts.append(
                        f"Commit {c.commit_sha[:8]} by {c.author} ({date_str}) [Bugfix: {c.is_bugfix}]\n"
                        f"Message: {c.message}\n"
                        f"Rationale: {c.original_decision_rationale or 'N/A'}"
                    )
                    sources.append({
                        "type": "historical_commit",
                        "path": f"commit/{c.commit_sha[:8]}",
                        "symbol": c.commit_sha[:8],
                        "summary": f"{c.message[:100]}",
                    })
                evidence_sections.append("=== HISTORICAL COMMITS & CHANGE RATIONALE ===\n" + "\n\n".join(commit_texts))

            # Recurring hotspots
            hotspots = self.db.query(RecurringIssueHotspot).filter(
                RecurringIssueHotspot.repository_id == repository_id
            ).order_by(desc(RecurringIssueHotspot.hotspot_score)).limit(3).all()
            if hotspots:
                hs_texts = [
                    f"Hotspot File: {h.file_path} (Severity: {h.severity.upper()}, Score: {h.hotspot_score}) - {h.bugfix_commits_count} bugfixes, {h.recurring_findings_count} review findings"
                    for h in hotspots
                ]
                evidence_sections.append("=== RECURRING ISSUE HOTSPOTS ===\n" + "\n".join(hs_texts))
                for h in hotspots:
                    sources.append({
                        "type": "recurring_hotspot",
                        "path": h.file_path,
                        "symbol": f"Hotspot:{h.file_path}",
                        "summary": f"{h.severity} hotspot (score: {h.hotspot_score})",
                    })

            # Evolution milestones
            milestones_q = self.db.query(HistoricalEvolutionMilestone).filter(
                HistoricalEvolutionMilestone.repository_id == repository_id
            )
            if words:
                m_conds = []
                for w in words[:3]:
                    m_conds.append(HistoricalEvolutionMilestone.title.ilike(f"%{w}%"))
                    m_conds.append(HistoricalEvolutionMilestone.problem_solved.ilike(f"%{w}%"))
                    m_conds.append(HistoricalEvolutionMilestone.module_name.ilike(f"%{w}%"))
                matching_milestones = milestones_q.filter(or_(*m_conds)).limit(4).all()
            else:
                matching_milestones = milestones_q.order_by(desc(HistoricalEvolutionMilestone.milestone_date)).limit(3).all()

            if not matching_milestones and ("architecture" in query.lower() or "evolv" in query.lower() or "change" in query.lower() or "refactor" in query.lower()):
                matching_milestones = milestones_q.order_by(desc(HistoricalEvolutionMilestone.milestone_date)).limit(4).all()

            if matching_milestones:
                m_texts = []
                for m in matching_milestones:
                    m_texts.append(
                        f"Milestone [{m.category.upper()}] - {m.title} (Module: {m.module_name}, Date: {m.milestone_date.strftime('%Y-%m-%d')})\n"
                        f"Previous Approach: {m.previous_approach}\n"
                        f"Current Approach: {m.current_approach}\n"
                        f"Problem Solved: {m.problem_solved}\n"
                        f"Reason for Change: {m.reason_for_change}\n"
                        f"Consequences: {m.consequences}"
                    )
                    sources.append({
                        "type": "evolution_milestone",
                        "path": f"milestone/{m.category}/{m.module_name}",
                        "symbol": m.title,
                        "summary": f"{m.category}: {m.problem_solved[:100]}",
                    })
                evidence_sections.append("=== ARCHITECTURE & SYSTEM EVOLUTION MILESTONES ===\n" + "\n\n".join(m_texts))

            # Historical bug lessons
            bug_q = self.db.query(HistoricalBugLesson).filter(
                HistoricalBugLesson.repository_id == repository_id
            )
            if "bug" in query.lower() or "issue" in query.lower() or "similar" in query.lower() or "prevent" in query.lower():
                matching_bugs = bug_q.limit(3).all()
            elif words:
                b_conds = []
                for w in words[:3]:
                    b_conds.append(HistoricalBugLesson.issue_title.ilike(f"%{w}%"))
                    b_conds.append(HistoricalBugLesson.description.ilike(f"%{w}%"))
                    b_conds.append(HistoricalBugLesson.module_name.ilike(f"%{w}%"))
                matching_bugs = bug_q.filter(or_(*b_conds)).limit(3).all()
            else:
                matching_bugs = []

            if matching_bugs:
                bug_texts = []
                for b in matching_bugs:
                    bug_texts.append(
                        f"Bug Lesson [{b.issue_category.upper()}] - {b.issue_title} (Module: {b.module_name})\n"
                        f"Description: {b.description}\n"
                        f"Root Cause: {b.root_cause}\n"
                        f"Resolution: {b.resolution_details}\n"
                        f"Preventative Rule: {b.prevention_recommendations}"
                    )
                    sources.append({
                        "type": "bug_lesson",
                        "path": f"bug/{b.module_name}/{b.issue_category}",
                        "symbol": b.issue_title,
                        "summary": f"[{b.issue_category}] {b.resolution_details[:100]}",
                    })
                evidence_sections.append("=== HISTORICAL BUG LESSONS & PREVENTATIVE RULES ===\n" + "\n\n".join(bug_texts))

        # -------------------------------------------------------------
        # 8. RAG VECTOR CHUNKS (Source code & documentation text chunks)
        # -------------------------------------------------------------
        try:
            chunks = self.rag_retriever.search(
                repository_id=repository_id,
                query_text=query,
                top_k=top_k,
                chunk_types=["documentation", "source_code", "test_code"],
            )
            if chunks:
                chunk_texts = []
                for c in chunks:
                    chunk_texts.append(f"--- File: {c.path} ({c.chunk_type}) ---\n{c.text}\n")
                    sources.append({
                        "type": c.chunk_type,
                        "path": c.path,
                        "symbol": c.path.split("/")[-1],
                        "summary": f"{c.chunk_type} chunk from {c.path}",
                    })
                evidence_sections.append("=== CODE & DOCUMENTATION EXCERPTS ===\n" + "\n".join(chunk_texts))
        except Exception as e:
            logger.warning(f"RAG search error during chat retrieval: {e}")

        # Combine all evidence
        has_grounded_evidence = len(evidence_sections) > 0
        evidence_text = "\n\n".join(evidence_sections) if has_grounded_evidence else "No relevant repository context found."

        # Deduplicate sources based on (type, path, symbol)
        unique_sources: List[Dict[str, Any]] = []
        seen_keys = set()
        for s in sources:
            key = (s.get("type"), s.get("path"), s.get("symbol"))
            if key not in seen_keys:
                seen_keys.add(key)
                unique_sources.append(s)

        return evidence_text, unique_sources, has_grounded_evidence
