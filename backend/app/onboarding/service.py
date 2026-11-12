"""
Onboarding & Codebase Blueprint Service — RepoMind 2.0.

Orchestrates:
  - Repository snapshot and document retrieval from PostgreSQL/pgvector
  - Atomic database-level locking and stale pending-job recovery
  - Grounded Gemini prompt assembly and strict path verification
  - Role-based learning track generation and caching
  - Private developer milestone progress tracking
"""
import hashlib
import json
import re
import logging
from typing import Set, List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.core.config import settings
from backend.app.organizations.models import Repository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.onboarding.models import RepositoryBlueprint, UserOnboardingProgress
from backend.app.onboarding.schemas import (
    LLMBlueprintPayload,
    RepositoryBlueprintResponse,
    UserProgressResponse,
    UpdateProgressRequest,
    TrackPlan,
    ReadingOrderItem,
    MilestoneItem,
    SubsystemItem,
    RequestFlowStep,
    CautionZone,
    SafeStarterArea,
)
from backend.app.onboarding.prompts import (
    ONBOARDING_SYSTEM_PROMPT,
    build_onboarding_user_content,
)
from backend.app.review.provider import get_llm_provider, LLMProviderError

logger = logging.getLogger(__name__)

GENERATION_TIMEOUT_SECONDS = 300  # 5 minutes before considering a pending job stale
MAX_GENERATION_RETRIES = 3


class OnboardingServiceError(Exception):
    """Base exception for onboarding operations."""
    pass


class UnindexedRepositoryError(OnboardingServiceError):
    """Raised when attempting to generate a blueprint for an unindexed repository."""
    pass


class GenerationInProgressError(OnboardingServiceError):
    """Raised when a blueprint generation job is currently in flight."""
    pass


class BlueprintGenerationError(OnboardingServiceError):
    """Raised when blueprint generation or parsing fails."""
    pass


class GroundingValidationError(OnboardingServiceError):
    """Raised when LLM output violates repository grounding rules."""
    pass


# ---------------------------------------------------------------------------
# Core Blueprint Service
# ---------------------------------------------------------------------------

class OnboardingService:
    def __init__(self, db: Session):
        self.db = db

    def get_indexed_snapshot_info(self, repository_id: int) -> Tuple[str, Set[str], List[Dict]]:
        """
        Fetch the verified repository snapshot from PostgreSQL:
        - Latest snapshot SHA or content hash
        - Full set of indexed file paths
        - Top-level doc chunks for LLM evidence
        """
        repo = self.db.get(Repository, repository_id)
        if not repo:
            raise OnboardingServiceError(f"Repository {repository_id} not found")

        # Must have indexed documents
        docs = self.db.execute(
            select(Document).where(Document.repository_id == repository_id)
        ).scalars().all()

        if not docs or repo.index_status != "indexed":
            raise UnindexedRepositoryError(
                f"Repository '{repo.github_name}' is not indexed. Please index the repository first."
            )

        indexed_paths = {doc.path for doc in docs}

        # Snapshot SHA: deterministic SHA-256 over all canonical indexed document paths and content hashes.
        # Explicitly reject simple [:40] truncation of concatenated strings so any document change invalidates cache.
        hasher = hashlib.sha256()
        for doc_path, doc_hash in sorted((d.path, d.content_hash or "") for d in docs):
            hasher.update(f"{doc_path}:{doc_hash}\n".encode("utf-8"))
        snapshot_sha = hasher.hexdigest()[:40]

        # Retrieve top documentation chunks for context
        doc_chunks = []
        stmt = (
            select(DocumentChunk)
            .where(
                and_(
                    DocumentChunk.repository_id == repository_id,
                    DocumentChunk.chunk_type.in_(["documentation", "source_code"]),
                )
            )
            .order_by(DocumentChunk.id)
            .limit(30)
        )
        chunks = self.db.execute(stmt).scalars().all()
        for c in chunks:
            doc_chunks.append({
                "file_path": c.file_path,
                "text": c.text,
                "chunk_type": c.chunk_type,
            })

        return snapshot_sha, indexed_paths, doc_chunks

    def get_or_generate_blueprint(
        self,
        repository_id: int,
        force_refresh: bool = False,
    ) -> RepositoryBlueprintResponse:
        """
        Retrieve cached blueprint or atomically claim generation lock.
        Validates commit SHA freshness and recovers from stale pending jobs.
        """
        now = datetime.now(timezone.utc)
        snapshot_sha, indexed_paths, doc_chunks = self.get_indexed_snapshot_info(repository_id)

        # 1. Atomic row lookup with write lock if mutating
        bp = self.db.query(RepositoryBlueprint).filter_by(repository_id=repository_id).first()

        # If a ready blueprint exists and not forcing refresh, return it immediately with staleness check
        if bp and bp.status == "ready" and not force_refresh:
            is_outdated = (bp.analyzed_commit_sha != snapshot_sha)
            logger.info(
                "Returning usable blueprint for repository %d (commit=%s, current=%s, outdated=%s)",
                repository_id,
                bp.analyzed_commit_sha,
                snapshot_sha,
                is_outdated,
            )
            return self._to_response(bp, snapshot_sha, is_outdated=is_outdated)

        # Handle concurrency & existing record
        if not bp:
            bp = RepositoryBlueprint(
                repository_id=repository_id,
                analyzed_commit_sha=snapshot_sha,
                status="pending",
                retry_count=0,
                generation_started_at=now,
            )
            self.db.add(bp)
            self.db.commit()
            self.db.refresh(bp)
        else:
            # Existing row: check if another job is currently active
            if bp.status == "pending" and bp.generation_started_at:
                elapsed = (now - bp.generation_started_at).total_seconds()
                if elapsed < GENERATION_TIMEOUT_SECONDS:
                    logger.warning("Blueprint generation already in progress for repo %d (elapsed %.1fs)", repository_id, elapsed)
                    raise GenerationInProgressError(
                        f"Blueprint generation is currently in progress ({int(elapsed)}s elapsed). Please retry shortly."
                    )
                else:
                    # Stale pending job recovery
                    logger.warning("Recovering stale pending blueprint generation for repo %d", repository_id)
                    bp.retry_count += 1
                    if bp.retry_count > MAX_GENERATION_RETRIES:
                        bp.status = "failed"
                        bp.generation_error = "Generation timed out and exceeded maximum retries."
                        self.db.commit()
                        raise BlueprintGenerationError(bp.generation_error)

            # Claim lock for regeneration
            bp.status = "pending"
            bp.generation_started_at = now
            self.db.commit()

        # Execute generation
        return self._execute_generation(bp, repository_id, snapshot_sha, indexed_paths, doc_chunks)

    def _execute_generation(
        self,
        bp: RepositoryBlueprint,
        repository_id: int,
        snapshot_sha: str,
        indexed_paths: Set[str],
        doc_chunks: List[Dict],
    ) -> RepositoryBlueprintResponse:
        """
        Calls Gemini, validates JSON output against Pydantic schema and grounding rules,
        and saves the blueprint atomically. Preserves prior valid blueprint if refresh fails.
        """
        repo = self.db.get(Repository, repository_id)
        now = datetime.now(timezone.utc)

        # Retain previous valid data in case regeneration fails
        prev_data = {
            "summary": bp.summary,
            "architecture_pattern": bp.architecture_pattern,
            "subsystems": bp.subsystems,
            "request_flow": bp.request_flow,
            "tracks": bp.tracks,
            "caution_zones": bp.caution_zones,
            "safe_starter_areas": bp.safe_starter_areas,
            "mermaid_diagram": bp.mermaid_diagram,
            "analyzed_commit_sha": bp.analyzed_commit_sha,
        }
        has_prior_valid = bp.summary is not None

        try:
            user_content = build_onboarding_user_content(
                repo_name=f"{repo.github_owner}/{repo.github_name}",
                default_branch=repo.default_branch,
                file_paths=list(indexed_paths),
                doc_chunks=doc_chunks,
            )

            llm = get_llm_provider(settings)
            raw_response = llm.complete(
                system_prompt=ONBOARDING_SYSTEM_PROMPT,
                user_content=user_content,
            )

            # Parse JSON
            payload = self._parse_and_validate_llm_response(raw_response, indexed_paths)

            # Update DB record with verified payload
            bp.status = "ready"
            bp.analyzed_commit_sha = snapshot_sha
            bp.summary = payload.summary
            bp.architecture_pattern = payload.architecture_pattern
            bp.subsystems = [s.model_dump() for s in payload.subsystems]
            bp.request_flow = [r.model_dump() for r in payload.request_flow]
            bp.tracks = {k: v.model_dump() for k, v in payload.tracks.items()}
            bp.caution_zones = [c.model_dump() for c in payload.caution_zones]
            bp.safe_starter_areas = [s.model_dump() for s in payload.safe_starter_areas]
            bp.mermaid_diagram = payload.mermaid_diagram
            bp.generation_completed_at = now
            bp.generation_error = None
            bp.retry_count = 0

            self.db.commit()
            self.db.refresh(bp)
            logger.info("Successfully generated blueprint for repository %d at commit %s", repository_id, snapshot_sha)
            return self._to_response(bp, snapshot_sha, is_outdated=False)

        except Exception as exc:
            logger.error("Blueprint generation failed for repository %d: %s", repository_id, exc, exc_info=True)
            self.db.rollback()

            # Reload bp in clean transaction
            bp = self.db.get(RepositoryBlueprint, bp.id)
            if has_prior_valid:
                # Preserve prior valid blueprint, record warning error
                bp.status = "ready"
                bp.summary = prev_data["summary"]
                bp.architecture_pattern = prev_data["architecture_pattern"]
                bp.subsystems = prev_data["subsystems"]
                bp.request_flow = prev_data["request_flow"]
                bp.tracks = prev_data["tracks"]
                bp.caution_zones = prev_data["caution_zones"]
                bp.safe_starter_areas = prev_data["safe_starter_areas"]
                bp.mermaid_diagram = prev_data["mermaid_diagram"]
                bp.analyzed_commit_sha = prev_data["analyzed_commit_sha"]
                bp.generation_error = f"Regeneration failed: {str(exc)}. Preserving last valid blueprint."
            else:
                bp.status = "failed"
                bp.generation_error = f"Generation failed: {str(exc)}"

            bp.generation_completed_at = now
            self.db.commit()
            raise BlueprintGenerationError(f"Failed to generate blueprint: {str(exc)}") from exc

    def _parse_and_validate_llm_response(
        self,
        raw_text: str,
        indexed_paths: Set[str],
    ) -> LLMBlueprintPayload:
        """
        Extracts JSON, validates against Pydantic schema, and performs strict
        repository grounding checks to prevent hallucinated file paths.
        """
        cleaned = raw_text.strip()
        # Strip markdown fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise BlueprintGenerationError(f"Malformed JSON returned by AI: {exc}") from exc

        # Pydantic validation
        try:
            payload = LLMBlueprintPayload.model_validate(data)
        except Exception as exc:
            raise BlueprintGenerationError(f"Blueprint schema validation failed: {exc}") from exc

        # Grounding Invariant: Validate referenced file paths against real indexed files
        self._enforce_grounding_invariants(payload, indexed_paths)

        return payload

    def _enforce_grounding_invariants(
        self,
        payload: LLMBlueprintPayload,
        indexed_paths: Set[str],
    ) -> None:
        """
        Validates that all paths mentioned in reading orders, request flow, and subsystems
        genuinely exist in the indexed repository snapshot.
        """
        # 1. Request flow files must exist
        for step in payload.request_flow:
            if step.file not in indexed_paths:
                raise GroundingValidationError(
                    f"Fabricated file path '{step.file}' in request_flow (not in indexed repository)"
                )

        # 2. Reading order files must exist in indexed repository
        for track_name, track in payload.tracks.items():
            valid_readings = []
            for item in track.reading_order:
                if item.file_path in indexed_paths:
                    valid_readings.append(item)
                else:
                    logger.warning(
                        "Dropping unverified file '%s' from track '%s' reading order",
                        item.file_path,
                        track_name,
                    )
            if not valid_readings:
                raise GroundingValidationError(
                    f"Track '{track_name}' contains zero verified repository files in its reading order."
                )
            track.reading_order = valid_readings

        # 3. Caution zones paths check (must match file or prefix directory)
        for zone in payload.caution_zones:
            path = zone.path.rstrip("/")
            path_exists = any(p == path or p.startswith(path + "/") for p in indexed_paths)
            if not path_exists:
                logger.warning("Caution zone '%s' does not match any indexed repository files", zone.path)

    def _to_response(
        self,
        bp: RepositoryBlueprint,
        current_indexed_sha: str,
        is_outdated: bool,
    ) -> RepositoryBlueprintResponse:
        """Construct typed response object from ORM entity."""
        tracks = {}
        if bp.tracks and isinstance(bp.tracks, dict):
            for k, v in bp.tracks.items():
                try:
                    tracks[k] = TrackPlan.model_validate(v)
                except Exception:
                    pass

        subsystems = []
        if bp.subsystems:
            for s in bp.subsystems:
                try:
                    subsystems.append(SubsystemItem.model_validate(s))
                except Exception:
                    pass

        request_flow = []
        if bp.request_flow:
            for r in bp.request_flow:
                try:
                    request_flow.append(RequestFlowStep.model_validate(r))
                except Exception:
                    pass

        caution_zones = []
        if bp.caution_zones:
            for c in bp.caution_zones:
                try:
                    caution_zones.append(CautionZone.model_validate(c))
                except Exception:
                    pass

        safe_starter_areas = []
        if bp.safe_starter_areas:
            for s in bp.safe_starter_areas:
                try:
                    safe_starter_areas.append(SafeStarterArea.model_validate(s))
                except Exception:
                    pass

        return RepositoryBlueprintResponse(
            repository_id=bp.repository_id,
            analyzed_commit_sha=bp.analyzed_commit_sha,
            status=bp.status,
            is_outdated=is_outdated,
            current_indexed_sha=current_indexed_sha,
            summary=bp.summary,
            architecture_pattern=bp.architecture_pattern,
            subsystems=subsystems,
            request_flow=request_flow,
            tracks=tracks,
            caution_zones=caution_zones,
            safe_starter_areas=safe_starter_areas,
            mermaid_diagram=bp.mermaid_diagram,
            retry_count=bp.retry_count,
            generation_error=bp.generation_error,
            created_at=bp.created_at,
            updated_at=bp.updated_at,
        )

    # -----------------------------------------------------------------------
    # User Progress (Anti-Surveillance & Private Checklist)
    # -----------------------------------------------------------------------

    def get_user_progress(self, user_id: int, repository_id: int) -> UserProgressResponse:
        """Fetch private progress for authenticated user."""
        progress = self.db.query(UserOnboardingProgress).filter_by(
            user_id=user_id,
            repository_id=repository_id,
        ).first()

        if not progress:
            # Create default empty progress row
            progress = UserOnboardingProgress(
                user_id=user_id,
                repository_id=repository_id,
                active_track="backend",
                completed_milestones=[],
                notes="",
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)

        return UserProgressResponse.model_validate(progress)

    def update_user_progress(
        self,
        user_id: int,
        repository_id: int,
        req: UpdateProgressRequest,
    ) -> UserProgressResponse:
        """Update private progress for authenticated user."""
        progress = self.db.query(UserOnboardingProgress).filter_by(
            user_id=user_id,
            repository_id=repository_id,
        ).first()

        if not progress:
            progress = UserOnboardingProgress(
                user_id=user_id,
                repository_id=repository_id,
                active_track=req.active_track or "backend",
                completed_milestones=req.completed_milestones or [],
                notes=req.notes or "",
            )
            self.db.add(progress)
        else:
            if req.active_track is not None:
                progress.active_track = req.active_track
            if req.completed_milestones is not None:
                progress.completed_milestones = req.completed_milestones
            if req.notes is not None:
                progress.notes = req.notes
            progress.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(progress)
        return UserProgressResponse.model_validate(progress)

