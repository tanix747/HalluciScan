import logging
import time
from uuid import uuid4

from app.claim_extractor import ClaimExtractor
from app.claim_extractor.exceptions import (
    ClaimExtractionConfigError,
    ClaimExtractionError,
    ClaimExtractionParseError,
    ClaimExtractionRateLimitError,
    ClaimExtractionTimeoutError,
)
from app.core.config import get_settings
from app.models.analysis import AnalyzeRequest, AnalyzeResponse, Claim, Evidence
from app.models.verification import VerificationResult
from app.reranker import Reranker
from app.reranker.exceptions import RerankingError
from app.retriever import Retriever
from app.retriever.exceptions import (
    RetrievalConfigError,
    RetrievalError,
    RetrievalRateLimitError,
    RetrievalTimeoutError,
)
from app.verifier import Verifier
from app.verifier.exceptions import (
    VerificationConfigError,
    VerificationError,
    VerificationParseError,
    VerificationRateLimitError,
    VerificationTimeoutError,
)

logger = logging.getLogger(__name__)


class AnalyzeValidationError(ValueError):
    pass


class AnalyzeProcessingError(Exception):
    pass


class AnalyzeDependencyConfigError(AnalyzeProcessingError):
    pass


class AnalyzeRateLimitError(AnalyzeProcessingError):
    pass


class AnalyzeTimeoutError(AnalyzeProcessingError):
    pass


class AnalyzeService:
    def __init__(
        self,
        claim_extractor: ClaimExtractor | None = None,
        retriever: Retriever | None = None,
        reranker: Reranker | None = None,
        verifier: Verifier | None = None,
    ) -> None:
        self._claim_extractor = claim_extractor
        self._retriever = retriever
        self._reranker = reranker
        self._verifier = verifier

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        started_at = time.perf_counter()
        normalized_text = request.text.strip()

        if not normalized_text:
            raise AnalyzeValidationError("text must not be empty")

        request_id = str(uuid4())

        try:
            settings = get_settings()
            claim_extractor = self._claim_extractor or ClaimExtractor(settings=settings)
            extracted_claims = await claim_extractor.extract(normalized_text)
            if not extracted_claims:
                processing_time_ms = int((time.perf_counter() - started_at) * 1000)
                logger.info(
                    "Analyze request completed with no factual claims",
                    extra={
                        "request_id": request_id,
                        "input_length": len(normalized_text),
                        "claim_count": 0,
                        "processing_time_ms": processing_time_ms,
                    },
                )
                return AnalyzeResponse(
                    request_id=request_id,
                    processing_time_ms=processing_time_ms,
                    claims=[],
                )

            retriever = self._retriever or Retriever(settings=settings)
            reranker = self._reranker or Reranker(settings=settings)
            verifier = self._verifier or Verifier(settings=settings)
        except ClaimExtractionParseError as exc:
            logger.warning("Claim extraction returned an invalid response", extra={"request_id": request_id})
            raise AnalyzeProcessingError("Claim extraction returned an invalid response") from exc
        except ClaimExtractionRateLimitError as exc:
            logger.warning("Claim extraction rate limited", extra={"request_id": request_id})
            raise AnalyzeRateLimitError("Claim extraction rate limited") from exc
        except ClaimExtractionTimeoutError as exc:
            logger.warning("Claim extraction timed out", extra={"request_id": request_id})
            raise AnalyzeTimeoutError("Claim extraction timed out") from exc
        except ClaimExtractionConfigError as exc:
            logger.error("Claim extraction is not configured", extra={"request_id": request_id})
            raise AnalyzeDependencyConfigError("Claim extraction is not configured") from exc
        except ClaimExtractionError as exc:
            logger.exception("Claim extraction failed", extra={"request_id": request_id})
            raise AnalyzeProcessingError("Claim extraction failed") from exc
        except (RetrievalConfigError, VerificationConfigError) as exc:
            logger.error("Pipeline dependency is not configured", extra={"request_id": request_id})
            raise AnalyzeDependencyConfigError(str(exc)) from exc

        claims = [
            await self._complete_claim(
                claim=claim,
                retriever=retriever,
                reranker=reranker,
                verifier=verifier,
                request_id=request_id,
            )
            for claim in extracted_claims
        ]

        processing_time_ms = int((time.perf_counter() - started_at) * 1000)

        logger.info(
            "Analyze request accepted",
            extra={
                "request_id": request_id,
                "input_length": len(normalized_text),
                "claim_count": len(claims),
                "processing_time_ms": processing_time_ms,
            },
        )

        return AnalyzeResponse(
            request_id=request_id,
            processing_time_ms=processing_time_ms,
            claims=claims,
        )

    async def _complete_claim(
        self,
        claim: Claim,
        retriever: Retriever,
        reranker: Reranker,
        verifier: Verifier,
        request_id: str,
    ) -> Claim:
        evidence = await self._retrieve_evidence(claim.text, retriever, request_id)
        ranked_evidence = await self._rerank_evidence(claim.text, evidence, reranker, request_id)
        verdict = await self._verify_claim(claim.text, ranked_evidence, verifier, request_id)

        return Claim(
            text=claim.text,
            status=verdict.status,
            confidence=verdict.confidence,
            reason=verdict.reason,
            evidence=ranked_evidence,
        )

    async def _retrieve_evidence(
        self,
        claim_text: str,
        retriever: Retriever,
        request_id: str,
    ) -> list[Evidence]:
        try:
            return await retriever.retrieve(claim_text)
        except (RetrievalRateLimitError, RetrievalTimeoutError, RetrievalError) as exc:
            logger.warning(
                "Evidence retrieval failed; continuing without evidence",
                extra={"request_id": request_id, "claim": claim_text, "error": str(exc)},
            )
            return []

    async def _rerank_evidence(
        self,
        claim_text: str,
        evidence: list[Evidence],
        reranker: Reranker,
        request_id: str,
    ) -> list[Evidence]:
        if not evidence:
            return []

        try:
            return await reranker.rerank(claim_text, evidence)
        except RerankingError as exc:
            logger.warning(
                "Evidence reranking failed; continuing with top retrieved evidence",
                extra={"request_id": request_id, "claim": claim_text, "error": str(exc)},
            )
            return evidence[:3]

    async def _verify_claim(
        self,
        claim_text: str,
        evidence: list[Evidence],
        verifier: Verifier,
        request_id: str,
    ) -> VerificationResult:
        try:
            return await verifier.verify(claim_text, evidence)
        except (
            VerificationParseError,
            VerificationRateLimitError,
            VerificationTimeoutError,
            VerificationError,
        ) as exc:
            logger.warning(
                "Claim verification failed; marking insufficient evidence",
                extra={"request_id": request_id, "claim": claim_text, "error": str(exc)},
            )
            return VerificationResult(
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                reason="Verification could not be completed for this claim.",
            )
