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

    def generate_content(self, **_kwargs: object) -> FakeGeminiResponse:
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
