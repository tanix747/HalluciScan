from fastapi.testclient import TestClient

from app.api.routes.analyze import get_analyze_service
from app.main import app
from app.models.analysis import AnalyzeRequest, AnalyzeResponse, Claim


client = TestClient(app)


class SuccessfulAnalyzeService:
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        return AnalyzeResponse(
            request_id="test-request-id",
            processing_time_ms=1,
            claims=[
                Claim(
                    text="Python was created by Guido van Rossum",
                    status=None,
                    confidence=None,
                    reason=None,
                    evidence=[],
                )
            ],
        )


def test_analyze_returns_extracted_claims_for_valid_request() -> None:
    app.dependency_overrides[get_analyze_service] = SuccessfulAnalyzeService

    response = client.post(
        "/api/analyze",
        json={"text": "Python was created by Guido van Rossum."},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["request_id"] == "test-request-id"
    assert body["processing_time_ms"] == 1
    assert body["claims"] == [
        {
            "text": "Python was created by Guido van Rossum",
            "status": None,
            "confidence": None,
            "reason": None,
            "evidence": [],
        }
    ]

    app.dependency_overrides.clear()


def test_analyze_rejects_empty_input() -> None:
    response = client.post("/api/analyze", json={"text": "   "})

    assert response.status_code == 422


def test_analyze_rejects_invalid_payload() -> None:
    response = client.post("/api/analyze", json={})

    assert response.status_code == 422
