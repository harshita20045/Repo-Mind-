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

  GeminiProvider  — calls Google's Gemini API using the google-generativeai SDK.
                    Requires LLM_PROVIDER=gemini and GEMINI_API_KEY set.
                    The google-generativeai package is an optional dependency; it is
                    imported lazily so LocalProvider works without it.
"""
import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Constants for Gemini provider
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"


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

    To perform real reviews, set LLM_PROVIDER=gemini and configure
    GEMINI_API_KEY in your .env file.
    """

    def complete(self, system_prompt: str, user_content: str) -> str:
        raise NotImplementedError(
            "LocalProvider is a development/null provider and cannot perform "
            "real LLM reviews. Set LLM_PROVIDER=gemini and configure "
            "GEMINI_API_KEY to use the Gemini provider."
        )


class GeminiProvider:
    """
    LLM provider backed by Google's Gemini API.

    Requires:
      - LLM_PROVIDER=gemini in environment/config
      - GEMINI_API_KEY set
      - google-genai installed

    The google-genai SDK is imported lazily so the module can be loaded without
    it when LLM_PROVIDER=local.
    """

    def __init__(self, api_key: str, model: str = GEMINI_DEFAULT_MODEL) -> None:
        self._api_key = api_key
        self._model = model

    def complete(self, system_prompt: str, user_content: str) -> str:
        """
        Call the Gemini API using the new google-genai SDK.

        Raises:
            LLMProviderError: On any Gemini API or network failure.
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise LLMProviderError(
                "google-genai package is not installed. "
                "Run: pip install google-genai"
            ) from exc

        try:
            client = genai.Client(api_key=self._api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
            )
            
            response = client.models.generate_content(
                model=self._model,
                contents=user_content,
                config=config
            )
            return response.text
        except Exception as exc:
            raise LLMProviderError(
                f"Unexpected error calling Gemini provider: {exc}"
            ) from exc


def get_llm_provider(settings) -> LLMProvider:
    """
    Factory: return the appropriate LLMProvider based on settings.

    This is the single authoritative location for provider selection.
    The review service must call this function; it must never instantiate
    GeminiProvider or LocalProvider directly.

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
            "Set LLM_PROVIDER=gemini to perform actual reviews."
        )
        return LocalProvider()

    if provider_name == "gemini":
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise LLMProviderError(
                "LLM_PROVIDER=gemini requires GEMINI_API_KEY to be set "
                "in the environment or .env file."
            )
        model = getattr(settings, "GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
        return GeminiProvider(api_key=api_key, model=model)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider_name}'. "
        "Supported values: 'local', 'gemini'."
    )
