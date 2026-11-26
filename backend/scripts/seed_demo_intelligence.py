"""
RepoMind Intelligence 2.0 — Comprehensive Demo Intelligence Seed Script
Idempotent, highly structured, enterprise-grade demonstration data populator.
"""
import os
import sys
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.orm import Session
from sqlalchemy import text, select

from backend.app.db import SessionLocal
from backend.app.core.config import settings
from backend.app.organizations.models import Project, Repository
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.onboarding.models import RepositoryBlueprint, UserOnboardingProgress
from backend.app.history.models import (
    ArchitectureDecisionRecord,
    HistoricalCommitRecord,
    RecurringIssueHotspot,
    HistoricalEvolutionMilestone,
    HistoricalBugLesson,
)
from backend.app.github.models import (
    PullRequest,
    PullRequestFile,
    PullRequestCommit,
    PullRequestEvent,
)
from backend.app.review.models import ReviewRun, Finding, FindingEvidence, HumanDecision
from backend.app.testing.models import TestScenario, GeneratedTestCase
from backend.app.impact.models import ChangeImpactAnalysis
from backend.app.intelligence.models import (
    CodeGraphNode,
    CodeGraphEdge,
    RepositoryScanSummary,
    PackageDependency,
)
from backend.app.rag.models import Document, DocumentChunk
from backend.app.rag.embedder import LocalEmbedder

from backend.scripts.demo_data.blueprint_data import BLUEPRINT_DATA
from backend.scripts.demo_data.adr_data import ADR_RECORDS
from backend.scripts.demo_data.commits_hotspots_data import COMMITS_DATA, HOTSPOTS_DATA
from backend.scripts.demo_data.prs_reviews_data import PRS_DATA
from backend.scripts.demo_data.rag_docs_data import RAG_DOCUMENTS
from backend.scripts.demo_data.evolution_data import (
    get_demo_evolution_milestones,
    get_demo_bug_lessons,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_demo_intelligence")

NOW = datetime.now(timezone.utc)
TARGET_REPO_ID = 1


def get_target_repo(db: Session) -> Repository:
    repo = db.get(Repository, TARGET_REPO_ID)
    if not repo:
        raise RuntimeError(f"Target repository {TARGET_REPO_ID} not found in database.")
    
    repo.default_branch = "main"
    repo.index_status = "indexed"
    repo.provider = "github"
    repo.github_url = "https://github.com/harshita20045/repomind-e2e-test-repository"
    repo.last_indexed_at = NOW
    db.commit()
    return repo


def seed_repository_scan_summary(db: Session, repo: Repository):
    logger.info("1/7 Seeding RepositoryScanSummary...")
    summary = db.query(RepositoryScanSummary).filter(RepositoryScanSummary.repository_id == repo.id).first()
    if not summary:
        summary = RepositoryScanSummary(repository_id=repo.id)
        db.add(summary)

    summary.primary_language = "Python"
    summary.languages = {"Python": 78.4, "Markdown": 15.2, "YAML": 4.1, "TOML": 2.3}
    summary.frameworks = ["FastAPI", "Pydantic V2", "SQLAlchemy", "PostgreSQL", "pytest", "Docker"]
    summary.entry_points = ["app/main.py", "app/api/users.py", "app/api/orders.py", "app/api/health.py"]
    summary.stats = {
        "files_count": 38,
        "lines_of_code": 4850,
        "functions_count": 52,
        "classes_count": 18,
        "nodes_count": 95,
        "edges_count": 142,
    }
    summary.architecture_summary = (
        "Enterprise-grade Order & User Management Platform designed with Layered Clean Architecture (Modular Monolith). "
        "Separates external HTTP routing (API), domain validation and business logic (Services), and persistence abstractions (Repositories) "
        "with strict dependency injection and isolated schema models."
    )
    summary.scanned_commit_sha = "8f3b9a1c4e7d2f0b8a6e4d2c0b8a6e4d2c0b8a6e"
    summary.mermaid_diagram = """flowchart TD
    Client["Client / WebApp / External Services"] --> Router["FastAPI Routing Layer (app/api)"]
    Router --> Dep["Dependency Injection & RBAC (app/dependencies.py)"]
    Dep --> Service["Business Services Layer (app/services)"]
    Service --> Models["Domain Entities & Schemas (app/models)"]
    Service --> Repos["Data Repositories (app/repositories)"]
    Repos --> Storage[("PostgreSQL / In-Memory Storage Engine")]
"""
    summary.updated_at = NOW
    db.commit()
    logger.info("  ✓ RepositoryScanSummary seeded.")


def seed_blueprint(db: Session, repo: Repository):
    logger.info("2/7 Seeding RepositoryBlueprint...")
    blueprint = db.query(RepositoryBlueprint).filter(RepositoryBlueprint.repository_id == repo.id).first()
    if not blueprint:
        blueprint = RepositoryBlueprint(
            repository_id=repo.id,
            analyzed_commit_sha="8f3b9a1c4e7d2f0b8a6e4d2c0b8a6e4d2c0b8a6e",
            status="ready",
        )
        db.add(blueprint)

    blueprint.status = "ready"
    blueprint.analyzed_commit_sha = "8f3b9a1c4e7d2f0b8a6e4d2c0b8a6e4d2c0b8a6e"
    blueprint.architecture_pattern = BLUEPRINT_DATA["architecture_pattern"]
    blueprint.summary = BLUEPRINT_DATA["summary"]
    blueprint.subsystems = BLUEPRINT_DATA["subsystems"]
    blueprint.request_flow = BLUEPRINT_DATA["request_flow"]
    blueprint.application_flows = BLUEPRINT_DATA["application_flows"]
    blueprint.lifecycle_diagram = BLUEPRINT_DATA["lifecycle_diagram"]
    blueprint.mermaid_diagram = BLUEPRINT_DATA["mermaid_diagram"]
    blueprint.caution_zones = BLUEPRINT_DATA["caution_zones"]
    blueprint.safe_starter_areas = BLUEPRINT_DATA["safe_starter_areas"]
    blueprint.glossary = BLUEPRINT_DATA["glossary"]
    blueprint.tracks = BLUEPRINT_DATA["tracks"]
    blueprint.updated_at = NOW
    db.commit()
    logger.info("  ✓ RepositoryBlueprint seeded.")


def seed_adrs(db: Session, repo: Repository):
    logger.info("3/7 Seeding Architecture Decision Records (ADRs)...")
    count = 0
    for adr_item in ADR_RECORDS:
        existing = (
            db.query(ArchitectureDecisionRecord)
            .filter(
                ArchitectureDecisionRecord.repository_id == repo.id,
                ArchitectureDecisionRecord.adr_number == adr_item["adr_number"],
            )
            .first()
        )
        if not existing:
            existing = ArchitectureDecisionRecord(
                repository_id=repo.id,
                adr_number=adr_item["adr_number"],
                title=adr_item["title"],
                status=adr_item["status"],
                context=adr_item["context"],
                decision=adr_item["decision"],
                options_considered=adr_item["options_considered"],
                reason=adr_item["reason"],
                consequences=adr_item["consequences"],
                superseded_alternative=adr_item.get("superseded_alternative"),
                file_source=adr_item.get("file_source"),
                affected_modules=adr_item["affected_modules"],
                date=adr_item["date"],
                decision_category=adr_item.get("decision_category", "architecture"),
                decision_type=adr_item.get("decision_type", "documented"),
                original_problem=adr_item.get("original_problem"),
                business_context=adr_item.get("business_context"),
                technical_context=adr_item.get("technical_context"),
                advantages=adr_item.get("advantages"),
                trade_offs=adr_item.get("trade_offs"),
                related_prs=adr_item.get("related_prs"),
                current_relevance=adr_item.get("current_relevance", "active"),
                created_at=NOW,
                updated_at=NOW,
            )
            db.add(existing)
            count += 1
        else:
            existing.title = adr_item["title"]
            existing.status = adr_item["status"]
            existing.context = adr_item["context"]
            existing.decision = adr_item["decision"]
            existing.options_considered = adr_item["options_considered"]
            existing.reason = adr_item["reason"]
            existing.consequences = adr_item["consequences"]
            existing.superseded_alternative = adr_item.get("superseded_alternative")
            existing.file_source = adr_item.get("file_source")
            existing.affected_modules = adr_item["affected_modules"]
            existing.decision_category = adr_item.get("decision_category", "architecture")
            existing.decision_type = adr_item.get("decision_type", "documented")
            existing.original_problem = adr_item.get("original_problem")
            existing.business_context = adr_item.get("business_context")
            existing.technical_context = adr_item.get("technical_context")
            existing.advantages = adr_item.get("advantages")
            existing.trade_offs = adr_item.get("trade_offs")
            existing.related_prs = adr_item.get("related_prs")
            existing.current_relevance = adr_item.get("current_relevance", "active")
            existing.updated_at = NOW
            count += 1
    db.commit()
    logger.info(f"  ✓ {count} ADR records synchronized.")


def seed_evolution_milestones_and_bug_lessons(db: Session, repo: Repository):
    logger.info("3.5/7 Seeding Evolution Milestones & Historical Bug Lessons...")
    milestones_data = get_demo_evolution_milestones(NOW)
    m_count = 0
    for m in milestones_data:
        m_date = NOW - timedelta(days=m["days_ago"])
        existing = (
            db.query(HistoricalEvolutionMilestone)
            .filter(
                HistoricalEvolutionMilestone.repository_id == repo.id,
                HistoricalEvolutionMilestone.title == m["title"],
            )
            .first()
        )
        # Find matching PR if exists
        pr = db.query(PullRequest).filter(
            PullRequest.repository_id == repo.id,
            PullRequest.github_number == m.get("pr_number")
        ).first()
        pr_id = pr.id if pr else None

        if not existing:
            existing = HistoricalEvolutionMilestone(
                repository_id=repo.id,
                milestone_date=m_date,
                title=m["title"],
                category=m["category"],
                module_name=m["module_name"],
                pr_id=pr_id,
                commit_sha=m.get("commit_sha"),
                previous_approach=m.get("previous_approach"),
                current_approach=m.get("current_approach"),
                problem_solved=m["problem_solved"],
                reason_for_change=m["reason_for_change"],
                business_context=m.get("business_context"),
                technical_explanation=m.get("technical_explanation"),
                affected_files=m.get("affected_files"),
                affected_modules=m.get("affected_modules"),
                dependencies_impacted=m.get("dependencies_impacted"),
                consequences=m.get("consequences"),
                lessons_learned=m.get("lessons_learned"),
                is_synthetic_demo=True,
                created_at=NOW,
            )
            db.add(existing)
            m_count += 1
        else:
            existing.milestone_date = m_date
            existing.category = m["category"]
            existing.module_name = m["module_name"]
            existing.pr_id = pr_id
            existing.commit_sha = m.get("commit_sha")
            existing.previous_approach = m.get("previous_approach")
            existing.current_approach = m.get("current_approach")
            existing.problem_solved = m["problem_solved"]
            existing.reason_for_change = m["reason_for_change"]
            existing.business_context = m.get("business_context")
            existing.technical_explanation = m.get("technical_explanation")
            existing.affected_files = m.get("affected_files")
            existing.affected_modules = m.get("affected_modules")
            existing.dependencies_impacted = m.get("dependencies_impacted")
            existing.consequences = m.get("consequences")
            existing.lessons_learned = m.get("lessons_learned")
            m_count += 1
    db.commit()
    logger.info(f"  ✓ {m_count} Evolution Milestones synchronized.")

    bug_lessons_data = get_demo_bug_lessons(NOW)
    b_count = 0
    for b in bug_lessons_data:
        b_date = NOW - timedelta(days=b["days_ago"])
        existing = (
            db.query(HistoricalBugLesson)
            .filter(
                HistoricalBugLesson.repository_id == repo.id,
                HistoricalBugLesson.issue_title == b["issue_title"],
            )
            .first()
        )
        if not existing:
            existing = HistoricalBugLesson(
                repository_id=repo.id,
                issue_title=b["issue_title"],
                issue_category=b["issue_category"],
                module_name=b["module_name"],
                description=b["description"],
                root_cause=b.get("root_cause"),
                related_pr_number=b.get("related_pr_number"),
                related_commit_sha=b.get("related_commit_sha"),
                files_involved=b.get("files_involved"),
                resolution_details=b["resolution_details"],
                tests_added=b.get("tests_added"),
                prevention_recommendations=b["prevention_recommendations"],
                warning_triggers=b.get("warning_triggers"),
                occurred_at=b_date,
                created_at=NOW,
            )
            db.add(existing)
            b_count += 1
        else:
            existing.issue_category = b["issue_category"]
            existing.module_name = b["module_name"]
            existing.description = b["description"]
            existing.root_cause = b.get("root_cause")
            existing.related_pr_number = b.get("related_pr_number")
            existing.related_commit_sha = b.get("related_commit_sha")
            existing.files_involved = b.get("files_involved")
            existing.resolution_details = b["resolution_details"]
            existing.tests_added = b.get("tests_added")
            existing.prevention_recommendations = b["prevention_recommendations"]
            existing.warning_triggers = b.get("warning_triggers")
            existing.occurred_at = b_date
            b_count += 1
    db.commit()
    logger.info(f"  ✓ {b_count} Historical Bug Lessons synchronized.")


def seed_commits_and_hotspots(db: Session, repo: Repository):
    logger.info("4/7 Seeding Historical Commits and Recurring Hotspots...")
    c_count = 0
    for c_item in COMMITS_DATA:
        existing = (
            db.query(HistoricalCommitRecord)
            .filter(
                HistoricalCommitRecord.repository_id == repo.id,
                HistoricalCommitRecord.commit_sha == c_item["commit_sha"],
            )
            .first()
        )
        if not existing:
            existing = HistoricalCommitRecord(
                repository_id=repo.id,
                commit_sha=c_item["commit_sha"],
                author=c_item["author"],
                committer=c_item["committer"],
                message=c_item["message"],
                committed_at=c_item["committed_at"],
                is_bugfix=c_item["is_bugfix"],
                files_changed=c_item["files_changed"],
                linked_issues=c_item["linked_issues"],
                original_decision_rationale=c_item["original_decision_rationale"],
                created_at=NOW,
            )
            db.add(existing)
            c_count += 1
        else:
            existing.message = c_item["message"]
            existing.is_bugfix = c_item["is_bugfix"]
            existing.files_changed = c_item["files_changed"]
            existing.original_decision_rationale = c_item["original_decision_rationale"]
            c_count += 1

    h_count = 0
    for h_item in HOTSPOTS_DATA:
        existing_h = (
            db.query(RecurringIssueHotspot)
            .filter(
                RecurringIssueHotspot.repository_id == repo.id,
                RecurringIssueHotspot.file_path == h_item["file_path"],
            )
            .first()
        )
        if not existing_h:
            existing_h = RecurringIssueHotspot(
                repository_id=repo.id,
                file_path=h_item["file_path"],
                total_commits=h_item["total_commits"],
                bugfix_commits_count=h_item["bugfix_commits_count"],
                recurring_findings_count=h_item["recurring_findings_count"],
                hotspot_score=h_item["hotspot_score"],
                severity=h_item["severity"],
                recurring_finding_categories=h_item["recurring_finding_categories"],
                historical_references=h_item["historical_references"],
                last_bugfix_at=h_item["last_bugfix_at"],
                created_at=NOW,
                updated_at=NOW,
            )
            db.add(existing_h)
            h_count += 1
        else:
            existing_h.total_commits = h_item["total_commits"]
            existing_h.bugfix_commits_count = h_item["bugfix_commits_count"]
            existing_h.recurring_findings_count = h_item["recurring_findings_count"]
            existing_h.hotspot_score = h_item["hotspot_score"]
            existing_h.severity = h_item["severity"]
            existing_h.recurring_finding_categories = h_item["recurring_finding_categories"]
            existing_h.historical_references = h_item["historical_references"]
            existing_h.updated_at = NOW
            h_count += 1

    db.commit()
    logger.info(f"  ✓ {c_count} Historical Commits and {h_count} Hotspots synchronized.")


def seed_prs_and_reviews(db: Session, repo: Repository):
    logger.info("5/7 Seeding Historical Pull Requests, Files, Commits, Reviews & Test Scenarios...")
    admin_user = db.query(User).first()
    admin_id = admin_user.id if admin_user else None

    pr_count = 0
    file_count = 0
    review_count = 0
    scenario_count = 0

    for pr_item in PRS_DATA:
        pr = (
            db.query(PullRequest)
            .filter(
                PullRequest.repository_id == repo.id,
                PullRequest.github_number == pr_item["github_number"],
            )
            .first()
        )
        if not pr:
            pr = PullRequest(
                repository_id=repo.id,
                github_number=pr_item["github_number"],
                title=pr_item["title"],
                state=pr_item["state"],
                description=pr_item["description"],
                author_user_id=admin_id,
                github_author_login=pr_item["author"],
                source_branch=pr_item["source_branch"],
                target_branch=pr_item["target_branch"],
                head_sha=pr_item["head_sha"],
                base_sha=pr_item["base_sha"],
                github_pr_id=f"PR_{repo.id}_{pr_item['github_number']}",
                github_url=f"https://github.com/harshita20045/repomind-e2e-test-repository/pull/{pr_item['github_number']}",
                created_at=pr_item["created_at"],
                merged_at=pr_item["merged_at"],
                updated_at=pr_item["merged_at"] or pr_item["created_at"],
                additions=pr_item["additions"],
                deletions=pr_item["deletions"],
                files_changed=pr_item["files_changed"],
                last_synced_at=NOW,
            )
            db.add(pr)
            db.flush()
        else:
            pr.title = pr_item["title"]
            pr.description = pr_item["description"]
            pr.state = pr_item["state"]
            pr.additions = pr_item["additions"]
            pr.deletions = pr_item["deletions"]
            pr.files_changed = pr_item["files_changed"]
            pr.head_sha = pr_item["head_sha"]
            pr.base_sha = pr_item["base_sha"]
            pr.source_branch = pr_item["source_branch"]
            pr.target_branch = pr_item["target_branch"]
            db.flush()
        pr_count += 1

        # Seed PullRequestFile records
        for f_item in pr_item.get("files", []):
            existing_f = (
                db.query(PullRequestFile)
                .filter(
                    PullRequestFile.pull_request_id == pr.id,
                    PullRequestFile.file_path == f_item["path"],
                )
                .first()
            )
            if not existing_f:
                existing_f = PullRequestFile(
                    pull_request_id=pr.id,
                    file_path=f_item["path"],
                    commit_sha=pr.head_sha,
                    status=f_item.get("status", "modified"),
                    additions=f_item.get("additions", 10),
                    deletions=f_item.get("deletions", 2),
                    changes=f_item.get("additions", 10) + f_item.get("deletions", 2),
                    patch_data=f"@@ -1,10 +1,15 @@\n+// Modified in {pr.title}\n",
                )
                db.add(existing_f)
                file_count += 1

        # Seed PullRequestCommit records
        existing_pr_c = (
            db.query(PullRequestCommit)
            .filter(
                PullRequestCommit.pull_request_id == pr.id,
                PullRequestCommit.sha == pr.head_sha,
            )
            .first()
        )
        if not existing_pr_c:
            pr_c = PullRequestCommit(
                pull_request_id=pr.id,
                sha=pr.head_sha,
                author=pr.github_author_login,
                committer=pr.github_author_login,
                message=pr.title,
                created_at=pr.created_at,
            )
            db.add(pr_c)

        # Seed ReviewRun & Findings
        review_run = (
            db.query(ReviewRun)
            .filter(ReviewRun.pull_request_id == pr.id)
            .first()
        )
        if not review_run:
            review_run = ReviewRun(
                pull_request_id=pr.id,
                commit_sha=pr.head_sha,
                status="completed",
                repomind_version="2.0.0",
                llm_model="groq/gpt-oss-120b",
                rag_enabled=True,
                started_at=pr.created_at,
                completed_at=pr.created_at + timedelta(seconds=14),
                intelligence_mode="deep_audit",
                progress_message="Review complete. Grounded evidence verified.",
                retry_count=0,
            )
            db.add(review_run)
            db.flush()
            review_count += 1

        # Seed Findings for the ReviewRun
        for f_item in pr_item.get("findings", []):
            existing_finding = (
                db.query(Finding)
                .filter(
                    Finding.review_run_id == review_run.id,
                    Finding.title == f_item["title"],
                )
                .first()
            )
            if not existing_finding:
                existing_finding = Finding(
                    review_run_id=review_run.id,
                    type=f_item["type"],
                    severity=f_item["severity"],
                    file=f_item["file"],
                    line=f_item["line"],
                    title=f_item["title"],
                    explanation=f_item["explanation"],
                    rule_source=f_item["rule_source"],
                    recommendation=f_item["recommendation"],
                    confidence=0.94,
                    status=f_item["status"],
                    evidence_status="verified",
                )
                db.add(existing_finding)
                db.flush()

                # Add FindingEvidence
                evidence = FindingEvidence(
                    finding_id=existing_finding.id,
                    evidence_status="verified",
                    source_type="ast_analysis",
                    source_path=f_item["file"],
                    source_text=f"Detected pattern violating {f_item['rule_source']} at line {f_item['line']}",
                )
                db.add(evidence)

        # Seed HumanDecision for closed PRs
        if pr.state == "closed":
            existing_decision = (
                db.query(HumanDecision)
                .filter(HumanDecision.review_run_id == review_run.id)
                .first()
            )
            if not existing_decision:
                decision = HumanDecision(
                    review_run_id=review_run.id,
                    user_id=admin_id,
                    action="approve",
                    target_type="pull_request",
                    target_id=pr.id,
                    note="LGTM — verified AI review findings and unit test coverage.",
                    created_at=pr.merged_at or pr.created_at,
                )
                db.add(decision)

        # Seed TestScenarios
        for ts_item in pr_item.get("test_scenarios", []):
            existing_ts = (
                db.query(TestScenario)
                .filter(
                    TestScenario.repository_id == repo.id,
                    TestScenario.pull_request_id == pr.id,
                    TestScenario.title == ts_item["title"],
                )
                .first()
            )
            if not existing_ts:
                existing_ts = TestScenario(
                    repository_id=repo.id,
                    pull_request_id=pr.id,
                    review_run_id=review_run.id,
                    target_file=ts_item["target_file"],
                    target_symbol=ts_item["target_symbol"],
                    category=ts_item["category"],
                    title=ts_item["title"],
                    description=ts_item["description"],
                    edge_case_notes="Generated by RepoMind Test Intelligence.",
                    suggested_assertions=[
                        "assert response.status_code == 200",
                        "assert result['status'] == 'confirmed'",
                    ],
                    existing_test_file="tests/test_orders.py",
                    coverage_gap=ts_item["coverage_gap"],
                    priority=ts_item["priority"],
                    created_at=NOW,
                )
                db.add(existing_ts)
                db.flush()
                scenario_count += 1

                # Add GeneratedTestCase
                test_case = GeneratedTestCase(
                    test_scenario_id=existing_ts.id,
                    language="python",
                    framework="pytest",
                    test_file_path=f"tests/generated/test_pr_{pr.github_number}.py",
                    test_code=f"""import pytest
from {ts_item['target_file'].replace('/', '.').replace('.py', '')} import {ts_item['target_symbol'].split('.')[-1]}

def test_{ts_item['category']}_{pr.github_number}():
    # Automated test case generated by RepoMind Test Intelligence
    pass
""",
                    execution_status="passed",
                    security_reviewed=True,
                    created_at=NOW,
                )
                db.add(test_case)

        # Seed ChangeImpactAnalysis
        impact_info = pr_item.get("impact", {})
        if impact_info:
            existing_impact = (
                db.query(ChangeImpactAnalysis)
                .filter(
                    ChangeImpactAnalysis.repository_id == repo.id,
                    ChangeImpactAnalysis.pull_request_id == pr.id,
                )
                .first()
            )
            
            # Build structured affected components
            seeded_affected_components = []
            seeded_test_recs = []
            for f in pr_item.get("files", []):
                f_path = f["path"]
                f_name = f_path.split("/")[-1]
                seeded_affected_components.append({
                    "name": f_name,
                    "component_name": f_name,
                    "file_path": f_path,
                    "component_type": "file",
                    "node_type": "file",
                    "impact_tier": "directly_affected",
                    "relationship": "modified",
                    "why_affected": f"Direct file modification in {f_path}",
                    "reason": f"Direct file modification in {f_path}",
                    "severity": "medium",
                    "distance": 0,
                    "supporting_evidence": f"File changed in PR #{pr.github_number}",
                    "evidence": f"File changed in PR #{pr.github_number}",
                    "suggested_verification": f"Run unit tests covering {f_name}",
                })
                raw_name = f_name.replace(".py", "").replace(".ts", "").replace(".js", "")
                test_file = f"test_{raw_name}.py"
                seeded_test_recs.append({
                    "target_component": f_name,
                    "target_file": f_path,
                    "recommended_test_file": test_file,
                    "test_type": "unit_test",
                    "priority": "P1_HIGH",
                    "reason": f"Directly modified component: verify internal logic of '{f_name}'.",
                    "command": f"pytest backend/tests/{test_file}",
                })

            seeded_breaking_changes = []
            if impact_info.get("breaking_changes_count", 0) > 0:
                first_file = pr_item.get("files", [{}])[0].get("path", "app/api/orders.py")
                seeded_breaking_changes.append({
                    "change_type": "contract_mutation",
                    "component_name": "API Error Response",
                    "file_path": first_file,
                    "severity": "high",
                    "title": "Legacy error string contract updated to RFC 7807",
                    "description": "Legacy error string contract updated to RFC 7807 problem details specification.",
                    "evidence": "Status response format changed from {'error': str} to RFC 7807 problem details dict.",
                    "suggested_fix": "Add backward-compatibility middleware or update client API consumers.",
                })

            seeded_graph_viz = {
                "nodes": [
                    {"id": f["path"], "label": f["path"].split("/")[-1], "tier": "directly_affected", "type": "file"}
                    for f in pr_item.get("files", [])
                ],
                "edges": [],
                "mermaid": f"flowchart LR\n    PR[\"PR #{pr.github_number}\"] --> M[\"Modified Files\"]",
            }

            if not existing_impact:
                existing_impact = ChangeImpactAnalysis(
                    repository_id=repo.id,
                    pull_request_id=pr.id,
                    review_run_id=review_run.id,
                    commit_sha=pr.head_sha,
                    target_branch=pr.target_branch,
                    risk_level=impact_info.get("risk_level", "low"),
                    directly_affected_count=impact_info.get("directly_affected_count", len(seeded_affected_components)),
                    indirectly_affected_count=impact_info.get("indirectly_affected_count", 0),
                    breaking_changes_count=impact_info.get("breaking_changes_count", len(seeded_breaking_changes)),
                    affected_components=seeded_affected_components,
                    breaking_changes=seeded_breaking_changes,
                    test_recommendations=seeded_test_recs,
                    graph_visualization=seeded_graph_viz,
                    summary=impact_info.get("summary", "Automated impact analysis complete."),
                    created_at=NOW,
                )
                db.add(existing_impact)
            else:
                existing_impact.affected_components = seeded_affected_components
                existing_impact.breaking_changes = seeded_breaking_changes
                existing_impact.test_recommendations = seeded_test_recs
                existing_impact.graph_visualization = seeded_graph_viz
                existing_impact.risk_level = impact_info.get("risk_level", existing_impact.risk_level)
                existing_impact.directly_affected_count = impact_info.get("directly_affected_count", len(seeded_affected_components))
                existing_impact.indirectly_affected_count = impact_info.get("indirectly_affected_count", existing_impact.indirectly_affected_count)
                existing_impact.breaking_changes_count = impact_info.get("breaking_changes_count", len(seeded_breaking_changes))
                existing_impact.summary = impact_info.get("summary", existing_impact.summary)

    db.commit()
    logger.info(f"  ✓ {pr_count} PRs, {file_count} PR Files, {review_count} Reviews, and {scenario_count} Test Scenarios synchronized.")


def seed_technical_debt(db: Session, repo: Repository):
    logger.info("6/7 Seeding Technical Debt Snapshots and Issues...")
    admin_user = db.query(User).first()
    admin_id = admin_user.id if admin_user else None

    snap_row = db.execute(
        text("SELECT id FROM technical_debt_snapshot WHERE repository_id = :rid"),
        {"rid": repo.id}
    ).fetchone()

    snapshot_id = None
    if not snap_row:
        cat_json = json.dumps({"architecture": 2, "security": 1, "test_coverage": 3, "code_smell": 2})
        mod_json = json.dumps(["app/services/order_service.py", "app/dependencies.py", "tests/test_orders.py"])
        ins_stmt = text("""
            INSERT INTO technical_debt_snapshot
            (repository_id, commit_sha, branch, health_score, total_issues, critical_issues, high_issues, medium_issues, low_issues, total_debt_hours, category_breakdown, most_affected_modules, scanned_files_count, scanned_lines_count, created_at)
            VALUES (:rid, :sha, :branch, 82, 8, 0, 2, 4, 2, 18.5, :cat, :mods, 38, 4850, :now)
            RETURNING id
        """)
        snapshot_id = db.execute(ins_stmt, {
            "rid": repo.id,
            "sha": "8f3b9a1c4e7d2f0b8a6e4d2c0b8a6e4d2c0b8a6e",
            "branch": "main",
            "cat": cat_json,
            "mods": mod_json,
            "now": NOW,
        }).scalar()
    else:
        snapshot_id = snap_row[0]

    issues_data = [
        {
            "category": "architecture",
            "severity": "high",
            "title": "Decouple UserRepository call inside OrderService",
            "explanation": "OrderService directly invokes UserRepository instead of accessing customer context via dependency injection.",
            "file_path": "app/services/order_service.py",
            "line_start": 34,
            "line_end": 42,
            "symbol_name": "OrderService.place_order",
            "recommended_action": "Pass resolved User customer entity directly into place_order method.",
            "estimated_remediation_hours": 3.0,
            "fingerprint": "debt_arch_01",
        },
        {
            "category": "test_coverage",
            "severity": "medium",
            "title": "Missing concurrency unit assertions for stock lock timeouts",
            "explanation": "When optimistic lock timeout occurs, exception fallback behavior is untested.",
            "file_path": "tests/test_orders.py",
            "line_start": 80,
            "line_end": 95,
            "symbol_name": "test_order_concurrency",
            "recommended_action": "Add pytest fixture simulating LockTimeoutException.",
            "estimated_remediation_hours": 2.5,
            "fingerprint": "debt_test_01",
        },
        {
            "category": "security",
            "severity": "high",
            "title": "Rotate JWT signing secret periodically",
            "explanation": "JWT signing secret does not implement automated key rotation mechanism.",
            "file_path": "app/dependencies.py",
            "line_start": 18,
            "line_end": 28,
            "symbol_name": "create_access_token",
            "recommended_action": "Integrate JWKS or dual-secret rotation algorithm.",
            "estimated_remediation_hours": 4.0,
            "fingerprint": "debt_sec_01",
        },
    ]

    for iss in issues_data:
        existing_iss = db.execute(
            text("SELECT id FROM technical_debt_issue WHERE repository_id = :rid AND fingerprint = :fp"),
            {"rid": repo.id, "fp": iss["fingerprint"]}
        ).fetchone()

        if not existing_iss:
            ins_issue = text("""
                INSERT INTO technical_debt_issue
                (repository_id, snapshot_id, category, severity, status, title, explanation, file_path, line_start, line_end, symbol_name, evidence, recommended_action, estimated_remediation_hours, fingerprint, created_at, updated_at)
                VALUES (:rid, :sid, :cat, :sev, 'open', :title, :expl, :fp_path, :ls, :le, :sym, :ev, :rec, :hours, :fp, :now, :now)
            """)
            db.execute(ins_issue, {
                "rid": repo.id,
                "sid": snapshot_id,
                "cat": iss["category"],
                "sev": iss["severity"],
                "title": iss["title"],
                "expl": iss["explanation"],
                "fp_path": iss["file_path"],
                "ls": iss["line_start"],
                "le": iss["line_end"],
                "sym": iss["symbol_name"],
                "ev": f"Static code audit at {iss['file_path']}:{iss['line_start']}",
                "rec": iss["recommended_action"],
                "hours": iss["estimated_remediation_hours"],
                "fp": iss["fingerprint"],
                "now": NOW,
            })

    db.commit()
    logger.info("  ✓ Technical Debt Snapshots and Issues synchronized.")


def seed_rag_documentation(db: Session, repo: Repository):
    logger.info("7/7 Seeding RAG Knowledge Documents & Embedding Chunks...")
    embedder = LocalEmbedder()
    doc_count = 0
    chunk_count = 0

    for doc_item in RAG_DOCUMENTS:
        content = doc_item["content"]
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        doc = (
            db.query(Document)
            .filter(
                Document.repository_id == repo.id,
                Document.path == doc_item["path"],
            )
            .first()
        )
        if not doc:
            doc = Document(
                repository_id=repo.id,
                path=doc_item["path"],
                content_hash=content_hash,
                updated_at=NOW,
            )
            db.add(doc)
            db.flush()
        else:
            doc.content_hash = content_hash
            doc.updated_at = NOW
            db.flush()
        doc_count += 1

        # Delete old chunks for this document to maintain idempotency
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.flush()

        # Split content into logical section chunks
        sections = [s.strip() for s in content.split("\n## ") if s.strip()]
        chunks_to_embed = []
        for idx, sec in enumerate(sections):
            chunk_text = f"## {sec}" if not sec.startswith("#") else sec
            chunks_to_embed.append(chunk_text)

        embeddings = embedder.embed_chunks(chunks_to_embed)

        for idx, (chunk_text, emb) in enumerate(zip(chunks_to_embed, embeddings)):
            chunk = DocumentChunk(
                document_id=doc.id,
                repository_id=repo.id,
                text=chunk_text,
                embedding=emb,
                chunk_index=idx,
                chunk_type="documentation",
                file_path=doc.path,
            )
            db.add(chunk)
            chunk_count += 1

    db.commit()
    logger.info(f"  ✓ {doc_count} Documentation files and {chunk_count} Vector Chunks embedded and indexed.")


def main():
    logger.info("=====================================================")
    logger.info("RepoMind Intelligence 2.0 — Seeding Demo Platform")
    logger.info("=====================================================")
    db = SessionLocal()
    try:
        repo = get_target_repo(db)
        logger.info(f"Target repository: {repo.github_owner}/{repo.github_name} (ID: {repo.id})")

        seed_repository_scan_summary(db, repo)
        seed_blueprint(db, repo)
        seed_adrs(db, repo)
        seed_evolution_milestones_and_bug_lessons(db, repo)
        seed_commits_and_hotspots(db, repo)
        seed_prs_and_reviews(db, repo)
        seed_technical_debt(db, repo)
        seed_rag_documentation(db, repo)

        logger.info("=====================================================")
        logger.info("🎉 DEMO INTELLIGENCE SEEDING COMPLETED SUCCESSFULLY!")
        logger.info("=====================================================")
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
