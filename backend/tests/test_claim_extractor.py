import pytest

from app.claim_extractor.exceptions import ClaimExtractionError, ClaimExtractionParseError
from app.claim_extractor.gemini import ClaimExtractor
from app.core.config import Settings


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeGeminiResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class FakeGeminiModels:
    def __init__(self, response_text: str | None = None, error: Exception | None = None) -> None:
        self._response_text = response_text
        self._error = error

    def generate_content(self, **_kwargs: object) -> FakeGeminiResponse:
        if self._error:
            raise self._error

        return FakeGeminiResponse(self._response_text)


class FakeGeminiClient:
    def __init__(self, response_text: str | None = None, error: Exception | None = None) -> None:
        self.models = FakeGeminiModels(response_text=response_text, error=error)


def make_settings() -> Settings:
    return Settings(GEMINI_API_KEY="test-key")


@pytest.mark.anyio
async def test_claim_extractor_returns_claims_from_gemini_json() -> None:
    extractor = ClaimExtractor(
        settings=make_settings(),
        client=FakeGeminiClient(
            response_text='{"claims":[{"text":"Python was created by Guido van Rossum"}]}'
        ),
    )

    claims = await extractor.extract(
        "Python was created by Guido van Rossum. Python is awesome."
    )

    assert len(claims) == 1
    assert claims[0].text == "Python was created by Guido van Rossum"
    assert claims[0].status is None
    assert claims[0].confidence is None
    assert claims[0].reason is None
    assert claims[0].evidence == []


@pytest.mark.anyio
async def test_claim_extractor_rejects_malformed_gemini_response() -> None:
    extractor = ClaimExtractor(settings=make_settings(), client=FakeGeminiClient("not json"))

    with pytest.raises(ClaimExtractionParseError):
        await extractor.extract("Python was created by Guido van Rossum.")


@pytest.mark.anyio
async def test_claim_extractor_rejects_empty_input() -> None:
    extractor = ClaimExtractor(
        settings=make_settings(),
        client=FakeGeminiClient('{"claims":[]}'),
    )

    with pytest.raises(ClaimExtractionParseError):
        await extractor.extract("   ")


@pytest.mark.anyio
async def test_claim_extractor_handles_api_failure() -> None:
    extractor = ClaimExtractor(
        settings=make_settings(),
        client=FakeGeminiClient(error=RuntimeError("service unavailable")),
    )

    with pytest.raises(ClaimExtractionError):
        await extractor.extract("Python was created by Guido van Rossum.")
