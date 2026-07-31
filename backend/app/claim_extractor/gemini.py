import json
import logging
import socket
from typing import Any

import httpx
import requests
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from app.claim_extractor.exceptions import (
    ClaimExtractionConfigError,
    ClaimExtractionError,
    ClaimExtractionParseError,
    ClaimExtractionRateLimitError,
    ClaimExtractionTimeoutError,
)
from app.core.config import Settings
from app.models.analysis import Claim

logger = logging.getLogger(__name__)


class ExtractedClaim(BaseModel):
    text: str = Field(..., min_length=1)


class ClaimExtractionResult(BaseModel):
    claims: list[ExtractedClaim] = Field(default_factory=list)


class ClaimExtractor:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if not settings.gemini_api_key:
            raise ClaimExtractionConfigError("GEMINI_API_KEY is not configured")

        self._settings = settings
        self._client = client or genai.Client(api_key=settings.gemini_api_key)

    async def extract(self, text: str) -> list[Claim]:
        normalized_text = text.strip()

        if not normalized_text:
            raise ClaimExtractionParseError("text must not be empty")

        logger.info("Starting Gemini claim extraction", extra={"input_length": len(normalized_text)})

        try:
            response_text = await run_in_threadpool(self._generate_claims, normalized_text)
            extraction = self._parse_response(response_text)
        except ClaimExtractionError:
            raise
        except errors.APIError as exc:
            self._handle_api_error(exc)
        except (TimeoutError, socket.timeout, httpx.TimeoutException, requests.exceptions.Timeout) as exc:
            raise ClaimExtractionTimeoutError("Gemini claim extraction timed out") from exc
        except Exception as exc:
            raise ClaimExtractionError("Gemini claim extraction failed") from exc

        logger.info("Gemini claim extraction completed", extra={"claim_count": len(extraction.claims)})

        return [
            Claim(
                text=extracted_claim.text,
                status=None,
                confidence=None,
                reason=None,
                evidence=[],
            )
            for extracted_claim in extraction.claims
        ]

    def _generate_claims(self, text: str) -> str:
        response = self._client.models.generate_content(
            model=self._settings.gemini_model,
            contents=self._build_prompt(text),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=ClaimExtractionResult.model_json_schema(),
                temperature=0,
                http_options=types.HttpOptions(timeout=self._settings.gemini_timeout_ms),
            ),
        )

        if not response.text:
            raise ClaimExtractionParseError("Gemini returned an empty response")

        return response.text

    def _parse_response(self, response_text: str) -> ClaimExtractionResult:
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            logger.warning("Gemini returned malformed JSON: %s", response_text)
            raise ClaimExtractionParseError("Gemini returned malformed JSON") from exc

        try:
            return ClaimExtractionResult.model_validate(payload)
        except ValidationError as exc:
            logger.warning("Gemini response failed schema validation: %s", exc)
            raise ClaimExtractionParseError("Gemini response did not match the claim schema") from exc

    def _handle_api_error(self, exc: errors.APIError) -> None:
        status_code = getattr(exc, "code", None) or getattr(exc, "status", None)

        if str(status_code) == "429":
            raise ClaimExtractionRateLimitError("Gemini rate limit exceeded") from exc

        raise ClaimExtractionError("Gemini API request failed") from exc

    def _build_prompt(self, text: str) -> str:
        return (
            "You are an information extraction system.\n\n"
            "Extract ONLY factual claims.\n"
            "Do not include opinions.\n"
            "Do not include assumptions.\n"
            "Do not explain anything.\n"
            "Return STRICT JSON.\n\n"
            "Example\n\n"
            "Input\n\n"
            "Python was created by Guido van Rossum.\n"
            "It first appeared in 1991.\n"
            "Python is awesome.\n\n"
            "Output\n\n"
            "{\n"
            '  "claims":[\n'
            "    {\n"
            '      "text":"Python was created by Guido van Rossum"\n'
            "    },\n"
            "    {\n"
            '      "text":"Python first appeared in 1991"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Ignore subjective statements.\n\n"
            f"Input\n\n{text}"
        )
