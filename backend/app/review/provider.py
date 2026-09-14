"""
LLM provider abstraction — Phase 8.

The review service depends on the LLMProvider Protocol, not on any concrete
SDK. Provider selection is centralised in get_llm_provider().

Per ADR-014 (no Docker) and ADR-011 (structured output), the provider must:
  - Accept a structured system prompt and user content separately.
  - Return the raw string response for the caller to validate.
  - Never receive PATs, GitHub tokens, or raw repository source code beyond
    the diff fragment already passed as untrusted evidence.

Providers:
  LocalProvider   — development/null provider. NOT a real LLM. Raises
                    NotImplementedError when asked to review, making its
                    null nature explicit and preventing it from being
                    mistaken for a real LLM review.

  ClaudeProvider  — calls Anthropic's Messages API using the anthropic SDK.
                    Requires LLM_PROVIDER=claude and ANTHROPIC_API_KEY set.
                    The anthropic package is an optional dependency; it is
                    imported lazily so LocalProvider works without it.
"""
import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Constants for Claude provider
CLAUDE_DEFAULT_MODEL = "claude-3-5-haiku-20241022"
CLAUDE_MAX_TOKENS = 4096


@runtime_checkable
class LLMProvider(Protocol):
    """
    Provider interface for the review service.
    Any object implementing complete() satisfies this protocol.
    """

    def complete(self, system_prompt: str, user_content: str) -> str:
        """
        Send a prompt to the LLM and return the raw text response.

        Args:
            system_prompt: Fixed instructions that must never contain
                           repository-sourced content.
            user_content:  Untrusted evidence (diff, retrieved chunks)
                           structurally separated from system_prompt.

        Returns:
            Raw string response. Caller is responsible for validation.

        Raises:
            LLMProviderError: On infrastructure/API failure.
        """
        ...


class LLMProviderError(Exception):
    """Raised on provider infrastructure failure (timeout, API error, etc.)."""


class LocalProvider:
    """
    Development/null provider. NOT a real LLM.

    This provider exists solely to allow the application to start and the
    module structure to be tested without a live LLM configuration. It
    explicitly signals that it cannot perform real reviews by raising
    NotImplementedError. This prevents null responses from being
    persisted as legitimate completed ReviewRuns.

    To perform real reviews, set LLM_PROVIDER=claude and configure
    ANTHROPIC_API_KEY in your .env file.
    """

    def complete(self, system_prompt: str, user_content: str) -> str:
        raise NotImplementedError(
            "LocalProvider is a development/null provider and cannot perform "
            "real LLM reviews. Set LLM_PROVIDER=claude and configure "
            "ANTHROPIC_API_KEY to use the Claude provider."
        )


class ClaudeProvider:
    """
    LLM provider backed by Anthropic's Claude API.

    Requires:
      - LLM_PROVIDER=claude in environment/config
      - ANTHROPIC_API_KEY set
      - anthropic>=0.40.0 installed

    The anthropic SDK is imported lazily so the module can be loaded without
    it when LLM_PROVIDER=local.
    """

    def __init__(self, api_key: str, model: str = CLAUDE_DEFAULT_MODEL) -> None:
        self._api_key = api_key
        self._model = model

    def complete(self, system_prompt: str, user_content: str) -> str:
        """
        Call the Anthropic Messages API.

        system_prompt and user_content are always kept as separate message
        roles — the API's system parameter and the user message respectively.
        Repository content in user_content can never bleed into the system
        instructions this way.

        Raises:
            LLMProviderError: On any Anthropic API or network failure.
        """
        try:
            import anthropic  # Lazy import — not required for LocalProvider
        except ImportError as exc:
            raise LLMProviderError(
                "anthropic package is not installed. "
                "Run: pip install anthropic>=0.40.0"
            ) from exc

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            message = client.messages.create(
                model=self._model,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            # Extract the text content from the first content block
            return message.content[0].text
        except anthropic.APIError as exc:
            raise LLMProviderError(
                f"Anthropic API error: {exc}"
            ) from exc
        except Exception as exc:
            raise LLMProviderError(
                f"Unexpected error calling LLM provider: {exc}"
            ) from exc


def get_llm_provider(settings) -> LLMProvider:
    """
    Factory: return the appropriate LLMProvider based on settings.

    This is the single authoritative location for provider selection.
    The review service must call this function; it must never instantiate
    ClaudeProvider or LocalProvider directly.

    Args:
        settings: The application Settings object (from core/config.py).

    Returns:
        An object satisfying the LLMProvider protocol.

    Raises:
        ValueError: If LLM_PROVIDER specifies an unknown provider.
        LLMProviderError: If required configuration (API key) is missing.
    """
    provider_name = (settings.LLM_PROVIDER or "local").lower()

    if provider_name == "local":
        logger.warning(
            "LLM_PROVIDER=local: using development/null provider. "
            "Real review requests will raise NotImplementedError. "
            "Set LLM_PROVIDER=claude to perform actual reviews."
        )
        return LocalProvider()

    if provider_name == "claude":
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            raise LLMProviderError(
                "LLM_PROVIDER=claude requires ANTHROPIC_API_KEY to be set "
                "in the environment or .env file."
            )
        model = getattr(settings, "CLAUDE_MODEL", CLAUDE_DEFAULT_MODEL)
        return ClaudeProvider(api_key=api_key, model=model)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider_name}'. "
        "Supported values: 'local', 'claude'."
    )
