import pytest

from app.core.config import Settings
from app.models.analysis import Evidence
from app.reranker.cross_encoder import Reranker


class FakeCrossEncoder:
    def predict(self, _pairs: list[tuple[str, str]]) -> list[float]:
        return [0.1, 0.9, 0.4, 0.7]


@pytest.mark.anyio
async def test_reranker_keeps_best_three_evidence_items() -> None:
    evidence = [
        Evidence(title="A", url="https://example.com/a", content="A"),
        Evidence(title="B", url="https://example.com/b", content="B"),
        Evidence(title="C", url="https://example.com/c", content="C"),
        Evidence(title="D", url="https://example.com/d", content="D"),
    ]
    reranker = Reranker(settings=Settings(RERANKER_TOP_K=3), model=FakeCrossEncoder())

    ranked = await reranker.rerank("claim", evidence)

    assert [item.title for item in ranked] == ["B", "D", "C"]
