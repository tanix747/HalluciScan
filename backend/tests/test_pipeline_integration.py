import pytest

from app.models.analysis import AnalyzeRequest, Claim, Evidence
from app.models.verification import VerificationResult
from app.retriever.exceptions import RetrievalError
from app.services.analyze_service import AnalyzeService


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeClaimExtractor:
    async def extract(self, _text: str) -> list[Claim]:
        return [Claim(text="Python was created by Guido van Rossum")]


class FakeRetriever:
    async def retrieve(self, _claim_text: str) -> list[Evidence]:
        return [
            Evidence(title="Python History", url="https://example.com/python", content="Python was created by Guido van Rossum."),
            Evidence(title="Programming Languages", url="https://example.com/languages", content="Python first appeared in 1991."),
            Evidence(title="Unrelated", url="https://example.com/other", content="This page is about another topic."),
            Evidence(title="Extra", url="https://example.com/extra", content="Python is a programming language."),
        ]


class FakeFailingRetriever:
    async def retrieve(self, _claim_text: str) -> list[Evidence]:
        raise RetrievalError("search failed")


class FakeReranker:
    async def rerank(self, _claim_text: str, evidence: list[Evidence]) -> list[Evidence]:
        return evidence[:3]


class FakeVerifier:
    async def verify(self, _claim_text: str, evidence: list[Evidence]) -> VerificationResult:
        if not evidence:
            return VerificationResult(
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                reason="No evidence was retrieved for this claim.",
            )

        return VerificationResult(
            status="SUPPORTED",
            confidence=0.94,
            reason="Multiple sources confirm the claim.",
        )


@pytest.mark.anyio
async def test_complete_pipeline_returns_verified_claim_with_top_evidence() -> None:
    service = AnalyzeService(
        claim_extractor=FakeClaimExtractor(),
        retriever=FakeRetriever(),
        reranker=FakeReranker(),
        verifier=FakeVerifier(),
    )

    response = await service.analyze(AnalyzeRequest(text="Python was created by Guido van Rossum."))

    assert len(response.claims) == 1
    claim = response.claims[0]
    assert claim.text == "Python was created by Guido van Rossum"
    assert claim.status == "SUPPORTED"
    assert claim.confidence == 0.94
    assert claim.reason == "Multiple sources confirm the claim."
    assert len(claim.evidence) == 3


@pytest.mark.anyio
async def test_pipeline_continues_when_retrieval_fails() -> None:
    service = AnalyzeService(
        claim_extractor=FakeClaimExtractor(),
        retriever=FakeFailingRetriever(),
        reranker=FakeReranker(),
        verifier=FakeVerifier(),
    )

    response = await service.analyze(AnalyzeRequest(text="Python was created by Guido van Rossum."))

    assert response.claims[0].status == "INSUFFICIENT_EVIDENCE"
    assert response.claims[0].evidence == []
