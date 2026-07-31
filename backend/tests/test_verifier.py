import pytest

from app.core.config import Settings
from app.models.analysis import Evidence
from app.verifier.exceptions import VerificationParseError
from app.verifier.gemini import Verifier


class FakeGeminiResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class FakeGeminiModels:
    def __init__(self, response_text: str | None) -> None:
        self._response_text = response_text
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> FakeGeminiResponse:
        self.calls.append(kwargs)
        return FakeGeminiResponse(self._response_text)


class FakeGeminiClient:
    def __init__(self, response_text: str | None) -> None:
        self.models = FakeGeminiModels(response_text)


def make_settings() -> Settings:
    return Settings(GEMINI_API_KEY="test-key")


@pytest.mark.anyio
async def test_verifier_returns_validated_gemini_verdict() -> None:
    verifier = Verifier(
        settings=make_settings(),
        client=FakeGeminiClient(
            '{"status":"SUPPORTED","confidence":0.91,"reason":"The evidence supports the claim."}'
        ),
    )
    evidence = [Evidence(title="Source", url="https://example.com", content="Supporting content")]

    result = await verifier.verify("A factual claim", evidence)

    assert result.status == "SUPPORTED"
    assert result.confidence == 0.91
    assert result.reason == "The evidence supports the claim."


@pytest.mark.anyio
async def test_verifier_rejects_malformed_gemini_response() -> None:
    verifier = Verifier(settings=make_settings(), client=FakeGeminiClient("not json"))
    evidence = [Evidence(title="Source", url="https://example.com", content="Supporting content")]

    with pytest.raises(VerificationParseError):
        await verifier.verify("A factual claim", evidence)


@pytest.mark.anyio
async def test_verifier_batch_returns_claim_ordered_results_from_gemini_json() -> None:
    client = FakeGeminiClient(
        '[{"claim":"Claim one","verdict":"SUPPORTED","confidence":0.91,"explanation":"Evidence supports it."},'
        '{"claim":"Claim two","verdict":"CONTRADICTED","confidence":0.82,"explanation":"Evidence contradicts it."}]'
    )
    verifier = Verifier(settings=make_settings(), client=client)

    results = await verifier.verify_batch(
        [
            ("Claim one", [Evidence(title="Source 1", url="https://example.com/1", content="Supporting content")]),
            ("Claim two", [Evidence(title="Source 2", url="https://example.com/2", content="Contradicting content")]),
        ]
    )

    assert len(client.models.calls) == 1
    assert [result.status for result in results] == ["SUPPORTED", "CONTRADICTED"]
    assert [result.reason for result in results] == ["Evidence supports it.", "Evidence contradicts it."]


def test_verifier_batch_prompt_truncates_evidence_content_and_preserves_source_fields() -> None:
    verifier = Verifier(settings=make_settings(), client=FakeGeminiClient("[]"))
    long_content = " ".join(["supporting-detail"] * 80)

    prompt = verifier._build_batch_prompt(
        [
            (
                "A factual claim",
                [Evidence(title="Long Source", url="https://example.com/source", content=long_content)],
            )
        ]
    )

    assert "Title: Long Source" in prompt
    assert "URL: https://example.com/source" in prompt
    assert "supporting-detail supporting-detail" in prompt
    assert long_content not in prompt
