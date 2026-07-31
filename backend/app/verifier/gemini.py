import json
import logging
import socket
from typing import Any

import httpx
import requests
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, RootModel, ValidationError
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.models.analysis import Evidence
from app.models.verification import VerificationResult, VerificationStatus
from app.verifier.exceptions import (
    VerificationConfigError,
    VerificationError,
    VerificationParseError,
    VerificationRateLimitError,
    VerificationTimeoutError,
)

logger = logging.getLogger(__name__)


class BatchVerificationItem(BaseModel):
    claim: str
    verdict: VerificationStatus
    confidence: float = Field(..., ge=0, le=1)
    explanation: str


class BatchVerificationResponse(RootModel[list[BatchVerificationItem]]):
    pass


class Verifier:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if not settings.gemini_api_key:
            raise VerificationConfigError("GEMINI_API_KEY is not configured")

        self._settings = settings
        self._client = client or genai.Client(api_key=settings.gemini_api_key)

    async def verify(self, claim_text: str, evidence: list[Evidence]) -> VerificationResult:
        if not evidence:
            return VerificationResult(
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                reason="No evidence was retrieved for this claim.",
            )

        try:
            response_text = await run_in_threadpool(self._generate_verdict, claim_text, evidence)
            result = self._parse_response(response_text)
        except VerificationError:
            raise
        except errors.APIError as exc:
            self._handle_api_error(exc)
        except (TimeoutError, socket.timeout, httpx.TimeoutException, requests.exceptions.Timeout) as exc:
            raise VerificationTimeoutError("Gemini verification timed out") from exc
        except Exception as exc:
            raise VerificationError("Gemini verification failed") from exc

        logger.info("Gemini verification completed", extra={"claim": claim_text, "status": result.status})
        return result

    async def verify_batch(self, claims_with_evidence: list[tuple[str, list[Evidence]]]) -> list[VerificationResult]:
        if not claims_with_evidence:
            return []

        try:
            response_text = await run_in_threadpool(self._generate_batch_verdicts, claims_with_evidence)
            results = self._parse_batch_response(response_text, claims_with_evidence)
        except VerificationError:
            raise
        except errors.APIError as exc:
            self._handle_api_error(exc)
        except (TimeoutError, socket.timeout, httpx.TimeoutException, requests.exceptions.Timeout) as exc:
            raise VerificationTimeoutError("Gemini verification timed out") from exc
        except Exception as exc:
            raise VerificationError("Gemini verification failed") from exc

        logger.info("Gemini batch verification completed", extra={"claim_count": len(results)})
        return results

    def _generate_verdict(self, claim_text: str, evidence: list[Evidence]) -> str:
        response = self._client.models.generate_content(
            model=self._settings.gemini_model,
            contents=self._build_prompt(claim_text, evidence),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=VerificationResult.model_json_schema(),
                temperature=0,
                http_options=types.HttpOptions(timeout=self._settings.gemini_timeout_ms),
            ),
        )

        if not response.text:
            raise VerificationParseError("Gemini returned an empty verification response")

        return response.text

    def _generate_batch_verdicts(self, claims_with_evidence: list[tuple[str, list[Evidence]]]) -> str:
        response = self._client.models.generate_content(
            model=self._settings.gemini_model,
            contents=self._build_batch_prompt(claims_with_evidence),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=BatchVerificationResponse.model_json_schema(),
                temperature=0,
                http_options=types.HttpOptions(timeout=self._settings.gemini_timeout_ms),
            ),
        )

        if not response.text:
            raise VerificationParseError("Gemini returned an empty verification response")

        return response.text

    def _parse_response(self, response_text: str) -> VerificationResult:
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            logger.warning("Gemini returned malformed verification JSON: %s", response_text)
            raise VerificationParseError("Gemini returned malformed verification JSON") from exc

        try:
            return VerificationResult.model_validate(payload)
        except ValidationError as exc:
            logger.warning("Gemini verification response failed schema validation: %s", exc)
            raise VerificationParseError("Gemini verification response did not match the schema") from exc

    def _parse_batch_response(
        self,
        response_text: str,
        claims_with_evidence: list[tuple[str, list[Evidence]]],
    ) -> list[VerificationResult]:
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            logger.warning("Gemini returned malformed batch verification JSON: %s", response_text)
            raise VerificationParseError("Gemini returned malformed verification JSON") from exc

        try:
            parsed = BatchVerificationResponse.model_validate(payload)
        except ValidationError as exc:
            logger.warning("Gemini batch verification response failed schema validation: %s", exc)
            raise VerificationParseError("Gemini verification response did not match the schema") from exc

        items = parsed.root
        if len(items) != len(claims_with_evidence):
            raise VerificationParseError("Gemini verification response did not include every claim")

        expected_claims = [claim_text for claim_text, _evidence in claims_with_evidence]
        if [item.claim for item in items] != expected_claims:
            raise VerificationParseError("Gemini verification response claims did not match the request")

        return [
            VerificationResult(
                status=item.verdict,
                confidence=item.confidence,
                reason=item.explanation,
            )
            for item in items
        ]

    def _handle_api_error(self, exc: errors.APIError) -> None:
        status_code = getattr(exc, "code", None) or getattr(exc, "status", None)

        if str(status_code) == "429":
            raise VerificationRateLimitError("Gemini verification rate limit exceeded") from exc

        raise VerificationError("Gemini verification request failed") from exc

    def _build_prompt(self, claim_text: str, evidence: list[Evidence]) -> str:
        evidence_block = "\n\n".join(
            (
                f"Evidence {index}\n"
                f"Title: {item.title}\n"
                f"URL: {item.url}\n"
                f"Content: {item.content}"
            )
            for index, item in enumerate(evidence, start=1)
        )

        return (
            "You are a factual claim verification system.\n\n"
            "Given one claim and the top evidence, return STRICT JSON only.\n"
            "Allowed status values are SUPPORTED, CONTRADICTED, and INSUFFICIENT_EVIDENCE.\n"
            "Use confidence as a number between 0 and 1.\n\n"
            "Claim\n"
            f"{claim_text}\n\n"
            "Top evidence\n"
            f"{evidence_block}\n\n"
            "Return JSON with exactly these fields: status, confidence, reason."
        )

    def _build_batch_prompt(self, claims_with_evidence: list[tuple[str, list[Evidence]]]) -> str:
        claims_block = "\n\n".join(
            self._format_claim_for_batch(index, claim_text, evidence)
            for index, (claim_text, evidence) in enumerate(claims_with_evidence, start=1)
        )

        return (
            "You are a factual claim verification system.\n\n"
            "Given all claims and their top evidence, verify every claim in one response.\n"
            "Allowed verdict values are SUPPORTED, CONTRADICTED, and INSUFFICIENT_EVIDENCE.\n"
            "Use confidence as a number between 0 and 1.\n"
            "When evidence is empty or inconclusive, use INSUFFICIENT_EVIDENCE.\n\n"
            f"{claims_block}\n\n"
            "Return STRICT JSON only: an array with one object per claim, in the same order as provided.\n"
            "Each object must contain exactly these fields: claim, verdict, confidence, explanation."
        )

    def _format_claim_for_batch(self, index: int, claim_text: str, evidence: list[Evidence]) -> str:
        evidence_block = "\n".join(
            (
                f"  Evidence {evidence_index}\n"
                f"  Title: {item.title}\n"
                f"  URL: {item.url}\n"
                f"  Snippet: {self._truncate_evidence_content(item.content)}"
            )
            for evidence_index, item in enumerate(evidence, start=1)
        )

        if not evidence_block:
            evidence_block = "  No evidence retrieved."

        return f"Claim {index}\nText: {claim_text}\nTop evidence:\n{evidence_block}"

    def _truncate_evidence_content(self, content: str, max_chars: int = 350) -> str:
        normalized = " ".join(content.split())
        if len(normalized) <= max_chars:
            return normalized

        truncated = normalized[:max_chars].rsplit(" ", 1)[0].rstrip(".,;:")
        return f"{truncated}..."
