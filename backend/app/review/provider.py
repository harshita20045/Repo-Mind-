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
        return (
            "**[Mock LLM Response]**\n\n"
            "This is a simulated response because you hit the API rate limit on your Gemini keys.\n"
            "You are currently using the local mock provider so you can continue testing the UI and functionality without errors."
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
            from google.genai.errors import APIError
        except ImportError as exc:
            raise LLMProviderError(
                "google-genai package is not installed. "
                "Run: pip install google-genai"
            ) from exc

        import tenacity
        
        def retry_if_transient_error(exception):
            if isinstance(exception, APIError):
                # Retry on 429 (Rate Limit) and 500, 502, 503, 504 (Server Errors)
                if exception.code in (429, 500, 502, 503, 504):
                    return True
            return False

        @tenacity.retry(
            retry=tenacity.retry_if_exception(retry_if_transient_error),
            wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
            stop=tenacity.stop_after_attempt(3),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                "Gemini transient failure (attempt %d). Retrying... Error: %s",
                retry_state.attempt_number, retry_state.outcome.exception()
            )
        )
        def _call_gemini():
            client = genai.Client(api_key=self._api_key)
            # Add reasonable timeout and deterministic temperature
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
            
            response = client.models.generate_content(
                model=self._model,
                contents=user_content,
                config=config
            )
            return response.text

        try:
            return _call_gemini()
        except APIError as exc:
            # Handle terminal APIError (e.g., 400, 401, 403, or max retries exhausted)
            raise LLMProviderError(
                f"Gemini API Error (status={exc.code}): {exc.message}"
            ) from exc
        except Exception as exc:
            raise LLMProviderError(
                f"Unexpected error calling Gemini provider: {exc}"
            ) from exc


class GroqProvider:
    """
    LLM provider backed by Groq API.
    
    Requires:
      - LLM_PROVIDER=groq in environment/config
      - GROQ_API_KEY set
      - groq installed
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def complete(self, system_prompt: str, user_content: str) -> str:
        """
        Call the Groq API using the official SDK.
        """
        try:
            from groq import Groq
            import groq
        except ImportError as exc:
            raise LLMProviderError(
                "groq package is not installed. "
                "Run: pip install groq"
            ) from exc

        import tenacity

        def retry_if_transient_error(exception):
            if isinstance(exception, groq.APIError):
                # groq.APIStatusError has status_code
                status = getattr(exception, "status_code", None)
                if status in (429, 500, 502, 503, 504):
                    return True
            return False

        @tenacity.retry(
            retry=tenacity.retry_if_exception(retry_if_transient_error),
            wait=tenacity.wait_exponential(multiplier=1, min=4, max=60),
            stop=tenacity.stop_after_attempt(3),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                "Groq transient failure (attempt %d). Retrying... Error: %s",
                retry_state.attempt_number, retry_state.outcome.exception()
            )
        )
        def _call_groq():
            client = Groq(api_key=self._api_key)
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content

        try:
            return _call_groq()
        except groq.APIStatusError as exc:
            raise LLMProviderError(
                f"Groq API Error (status={exc.status_code}): {exc.message}"
            ) from exc
        except Exception as exc:
            raise LLMProviderError(
                f"Unexpected error calling Groq provider: {exc}"
            ) from exc


class FallbackProvider:
    """
    Attempts to use the primary provider. If it fails (e.g., due to quota, invalid key),
    falls back to the secondary provider.
    """
    def __init__(self, primary: LLMProvider, secondary: LLMProvider):
        self._primary = primary
        self._secondary = secondary

    def complete(self, system_prompt: str, user_content: str) -> str:
        try:
            return self._primary.complete(system_prompt, user_content)
        except LLMProviderError as exc:
            logger.warning(f"Primary provider failed: {exc}. Falling back to secondary provider.")
            return self._secondary.complete(system_prompt, user_content)


def get_llm_provider(settings) -> LLMProvider:
    if settings.LLM_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise LLMProviderError("GEMINI_API_KEY is missing for LLM_PROVIDER=gemini")
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    elif settings.LLM_PROVIDER == "groq":
        # The user requested Groq with fallback to Gemini.
        # We instantiate both if possible.
        providers = []
        if settings.GROQ_API_KEY:
            providers.append(GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL))
        
        if settings.GEMINI_API_KEY:
            providers.append(GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL))
            
        if len(providers) == 2:
            return FallbackProvider(primary=providers[0], secondary=providers[1])
        elif len(providers) == 1:
            return providers[0]
        else:
            raise LLMProviderError("Neither GROQ_API_KEY nor GEMINI_API_KEY is available for LLM_PROVIDER=groq")
    else:
        logger.warning("Forcing LocalProvider for testing or unknown LLM_PROVIDER.")
        return LocalProvider()
