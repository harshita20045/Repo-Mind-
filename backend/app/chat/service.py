"""
Chat Assistant Service — RepoMind 2.0.

Manages conversational sessions scoped to PRs, repositories, or reviews.
Integrates Multi-Source Context Retrieval and Query Classification across 7 context sources:
1. Source code & AST symbols
2. Documentation & architecture blueprint
3. Architecture rules & constraints
4. Dependency graph & call chains
5. Pull request diffs
6. Review findings
7. Historical human decisions & test intelligence
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.chat.models import ChatSession, ChatMessage
from backend.app.chat.classifier import classify_query, QueryIntent, ExtractedEntities
from backend.app.chat.retrieval import MultiSourceContextRetriever
from backend.app.review.provider import LLMProvider
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_CHAT_PROMPT = """You are RepoMind, an expert enterprise repository intelligence assistant.
You are currently engaged in a conversation scoped to a {context_type}.

You have access to 7 contextual intelligence sources from this repository:
1. Source code & AST symbols (definitions, lines, keys)
2. Documentation & architecture blueprint (application flows, entry points)
3. Architecture rules & constraints (rule codes, forbidden dependencies, layer rules)
4. Dependency graph & call chains (incoming callers, outgoing callees, dependencies)
5. Pull request diffs (changed files, patch hunks, status)
6. Review findings (audit findings, severities, rule sources)
7. Historical human decisions & test intelligence (scenarios, coverage gaps, decisions)

CRITICAL RULES:
1. Always base your answers strictly on the provided EVIDENCE below.
2. If the EVIDENCE does not contain the answer or is insufficient, explicitly state:
   "I don't have enough evidence in the repository context to answer that."
3. NEVER fabricate, invent, or guess file paths, function names, API endpoints, or database structures.
4. Structure your response with the following sections when answering technical questions:
   - **Explanation**: A clear, grounded explanation of how it works or what was asked.
   - **Relevant Files**: The exact repository file paths involved (from the evidence).
   - **Relevant Functions / Symbols**: The exact functions, classes, or endpoints involved.
   - **Source References**: Specific citations referencing the evidence (e.g. Rule code, AST node, PR diff, Doc chunk).

EVIDENCE:
{evidence}
"""


def create_session(
    db: Session,
    user_id: int,
    organization_id: int,
    context_type: str,
    context_id: int
) -> ChatSession:
    """Create a new chat session."""
    session = ChatSession(
        user_id=user_id,
        organization_id=organization_id,
        context_type=context_type,
        context_id=context_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_sessions(db: Session, user_id: int, context_type: str, context_id: int) -> List[ChatSession]:
    """Get chat sessions for a user in a specific context."""
    stmt = select(ChatSession).where(
        ChatSession.user_id == user_id,
        ChatSession.context_type == context_type,
        ChatSession.context_id == context_id
    ).order_by(ChatSession.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_session_messages(db: Session, session_id: int, user_id: int) -> List[ChatMessage]:
    """Get all messages for a session (must belong to user)."""
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        return []
        
    stmt = select(ChatMessage).where(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def send_message(
    db: Session,
    session_id: int,
    user_id: int,
    message: str,
    provider: LLMProvider,
    repository_id: Optional[int],
) -> ChatMessage:
    """
    Send a message in a chat session.
    Retrieves multi-source repository context, classifies intent, and queries the LLM.
    Strictly verifies organization & repository isolation.
    """
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise ValueError("Session not found or access denied")

    # 1. Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=message
    )
    db.add(user_msg)

    # 2. Query classification & multi-source retrieval with strict tenant boundary check
    unique_sources: List[Dict[str, Any]] = []
    has_grounded_evidence = False
    evidence_text = "No relevant repository context found."

    if repository_id is not None:
        from backend.app.organizations.models import Repository
        repo = db.get(Repository, repository_id)
        if not repo or repo.project.organization_id != session.organization_id:
            raise ValueError("Unauthorized repository access")

        entities = classify_query(
            text=message,
            context_type=session.context_type,
            context_id=session.context_id,
        )

        retriever = MultiSourceContextRetriever(db=db)
        evidence_text, unique_sources, has_grounded_evidence = retriever.retrieve(
            repository_id=repository_id,
            query=message,
            entities=entities,
            top_k=5,
        )

    # 3. Build system prompt
    system_prompt = SYSTEM_CHAT_PROMPT.format(
        context_type=session.context_type,
        evidence=evidence_text
    )

    # 4. Fetch previous history for multi-turn context (last 6 messages)
    history = get_session_messages(db, session_id, user_id)
    history_items = []
    for msg in history[-6:]:
        history_items.append(f"{msg.role.upper()}: {msg.content}")
    history_text = "\n\n".join(history_items) if history_items else "No previous history."
    user_content = f"Recent Conversation History:\n{history_text}\n\nCurrent User Question:\n{message}"

    # 5. Call LLM
    try:
        if not has_grounded_evidence and repository_id is not None:
            # Explicit evidence insufficiency response when no repository context could be matched
            response_content = (
                "I don't have enough evidence in the repository context to answer that.\n\n"
                "Please verify that the repository has been indexed and that the module, symbol, or question "
                "matches the current codebase."
            )
            is_grounded = False
        else:
            raw_response = provider.complete(system_prompt, user_content)
            
            # If LocalProvider mock is returned and we have evidence, provide a well-structured grounded response
            if "Mock LLM Response" in raw_response and has_grounded_evidence:
                response_content = _build_grounded_mock_response(message, unique_sources, evidence_text)
            else:
                response_content = raw_response
            is_grounded = has_grounded_evidence
    except Exception as e:
        logger.error(f"LLM Chat Error: {e}")
        response_content = "I'm sorry, I encountered an error while processing your request."
        is_grounded = False

    # 6. Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response_content,
        sources=unique_sources,
        is_grounded=is_grounded
    )
    db.add(assistant_msg)

    # Update session
    session.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


def _build_grounded_mock_response(message: str, sources: List[Dict[str, Any]], evidence_text: str) -> str:
    """
    Builds a grounded, evidence-backed response when running under LocalProvider.
    Ensures that Explanation, Relevant Files, Relevant Functions/Symbols, and Source References
    are strictly populated from the retrieved repository evidence.
    """
    files = list({s["path"] for s in sources if s.get("path") and not s["path"].startswith("Rule:") and not s["path"].startswith("Repository")})
    symbols = list({s["symbol"] for s in sources if s.get("symbol")})
    citations = list({f"[{s.get('type')}] {s.get('path')} ({s.get('summary', '')})" for s in sources[:6]})

    explanation = f"Based on the repository intelligence retrieved for: '{message}'\n\n"
    explanation += "The codebase contains matching entities and structural definitions as detailed in the evidence below."

    files_section = "\n".join([f"- `{f}`" for f in files]) if files else "- None specified in repository evidence."
    symbols_section = "\n".join([f"- `{sym}`" for sym in symbols]) if symbols else "- None identified."
    citations_section = "\n".join([f"- {c}" for c in citations]) if citations else "- Repository Scan / Context"

    return (
        f"### Explanation\n{explanation}\n\n"
        f"### Relevant Files\n{files_section}\n\n"
        f"### Relevant Functions / Symbols\n{symbols_section}\n\n"
        f"### Source References\n{citations_section}"
    )
