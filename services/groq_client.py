from __future__ import annotations

import logging
import random
import time
from typing import Any

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    Groq,
    RateLimitError,
)
from pydantic import SecretStr

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq chat-completions client with bounded retries and useful diagnostics."""

    def __init__(
        self,
        api_key: SecretStr,
        model: str = "openai/gpt-oss-120b",
        timeout: float = 60.0,
        max_retries: int = 1,
    ) -> None:
        key = api_key.get_secret_value().strip()

        if not key:
            raise ValueError("Groq API key is not configured.")
        if not model.strip():
            raise ValueError("Model name cannot be empty.")
        if timeout <= 0:
            raise ValueError("Timeout must be greater than zero.")
        if max_retries < 0:
            raise ValueError("Max retries cannot be negative.")

        self.model = model
        self.max_retries = max_retries
        self._client = Groq(
            api_key=key,
            timeout=timeout,
            max_retries=0,
        )

    @staticmethod
    def _validate_prompt(system_prompt: str, user_prompt: str) -> None:
        if not isinstance(system_prompt, str) or not system_prompt.strip():
            raise ValueError("System prompt cannot be empty.")
        if not isinstance(user_prompt, str) or not user_prompt.strip():
            raise ValueError("User prompt cannot be empty.")

    @staticmethod
    def _retry_after(exc: Exception) -> float | None:
        """Read Retry-After safely; return None if the header is absent/invalid."""
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None)
        if headers is None:
            return None

        value = headers.get("retry-after")
        if value is None:
            return None

        try:
            return max(0.0, min(float(value), 30.0))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_error_code(exc: Exception) -> str | None:
        """Extract a short provider error code without logging credentials or prompts."""
        body: Any = getattr(exc, "body", None)
        if not isinstance(body, dict):
            return None

        error = body.get("error", body)
        if isinstance(error, dict):
            code = error.get("code") or error.get("type")
            if isinstance(code, (str, int)):
                return str(code)[:100]
        return None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a response, retrying transient errors a bounded number of times."""
        self._validate_prompt(system_prompt, user_prompt)

        if not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2.")
        if max_tokens < 1:
            raise ValueError("max_tokens must be positive.")

        total_characters = len(system_prompt) + len(user_prompt)
        if total_characters > 100_000:
            raise ValueError(
                "Prompt bohat bara hai. Research notes aur input ko "
                "short karke dobara try karo."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if not response.choices:
                    raise RuntimeError("AI ne koi response return nahi kiya.")

                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise RuntimeError("AI ne empty response return kiya.")

                return content.strip()

            except RateLimitError as exc:
                retry_after = self._retry_after(exc)
                error_code = self._safe_error_code(exc)
                logger.warning(
                    "Groq HTTP 429. model=%s attempt=%s/%s retry_after=%s error_code=%s",
                    self.model,
                    attempt + 1,
                    self.max_retries + 1,
                    retry_after,
                    error_code or "not provided",
                )

                if attempt < self.max_retries:
                    delay = (
                        retry_after
                        if retry_after is not None
                        else min(2 ** attempt + random.random(), 8.0)
                    )
                    time.sleep(delay)
                    continue

                retry_text = (
                    f" Provider Retry-After: {retry_after:g} seconds."
                    if retry_after is not None
                    else ""
                )
                code_text = f" Error code: {error_code}." if error_code else ""
                raise RuntimeError(
                    "Groq ne HTTP 429 (rate limit/quota) return kiya."
                    f"{retry_text}{code_text} "
                    "Groq Console mein is model ki usage, RPM/TPM/RPD/TPD "
                    "limits aur billing/quota check karo. Agar limit reset "
                    "ka wait karna ho to baad mein retry karo."
                ) from None

            except APIStatusError as exc:
                status_code = getattr(exc, "status_code", None)
                error_code = self._safe_error_code(exc)
                logger.error(
                    "Groq API HTTP %s. model=%s error_code=%s",
                    status_code,
                    self.model,
                    error_code or "not provided",
                )

                if status_code == 413:
                    message = (
                        "Groq request payload bohat bara hai (HTTP 413). "
                        "Prompt aur research notes ko chhota karna hoga."
                    )
                elif status_code == 401:
                    message = (
                        "Groq API key authenticate nahi hui (HTTP 401). "
                        "Console mein key aur .env configuration check karo."
                    )
                elif status_code == 403:
                    message = (
                        "Groq ne request access deny ki (HTTP 403). "
                        "Project permissions, model access aur account status check karo."
                    )
                elif status_code == 429:
                    message = (
                        "Groq ne HTTP 429 return kiya. Model ki usage aur "
                        "rate limits/quota check karo."
                    )
                elif status_code == 400:
                    message = (
                        "Groq ne request reject ki (HTTP 400). Model name, "
                        "prompt aur request parameters check karo."
                    )
                else:
                    message = (
                        f"Groq API ne HTTP {status_code} return kiya. "
                        "Terminal logs aur Groq Console check karo."
                    )

                if error_code:
                    message += f" Provider error code: {error_code}."
                raise RuntimeError(message) from None

            except (APIConnectionError, APITimeoutError) as exc:
                logger.warning(
                    "Groq network error. model=%s attempt=%s/%s type=%s",
                    self.model,
                    attempt + 1,
                    self.max_retries + 1,
                    type(exc).__name__,
                )

                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 4))
                    continue

                raise RuntimeError(
                    "Groq se connection nahi ho saka ya request timeout hui. "
                    "Internet/network check karo aur dobara try karo."
                ) from None

        raise RuntimeError("Groq request complete nahi ho saki.")
