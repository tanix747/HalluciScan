import logging
from typing import Any

from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.models.analysis import Evidence
from app.reranker.exceptions import RerankingError

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, settings: Settings, model: Any | None = None) -> None:
        self._settings = settings
        self._model = model

    async def rerank(self, claim_text: str, evidence: list[Evidence]) -> list[Evidence]:
        if not evidence:
            return []

        try:
            scored = await run_in_threadpool(self._score, claim_text, evidence)
        except Exception as exc:
            raise RerankingError("Evidence reranking failed") from exc

        ranked = [
            item
            for item, _score in sorted(
                scored,
                key=lambda item_with_score: item_with_score[1],
                reverse=True,
            )
        ]

        top_evidence = ranked[: self._settings.reranker_top_k]
        logger.info(
            "Reranked evidence",
            extra={"claim": claim_text, "input_count": len(evidence), "output_count": len(top_evidence)},
        )

        return top_evidence

    def _score(self, claim_text: str, evidence: list[Evidence]) -> list[tuple[Evidence, float]]:
        model = self._model or self._load_model()
        pairs = [(claim_text, item.content) for item in evidence]
        scores = model.predict(pairs)

        return [(item, float(score)) for item, score in zip(evidence, scores, strict=False)]

    def _load_model(self) -> Any:
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(self._settings.reranker_model)
        return self._model
