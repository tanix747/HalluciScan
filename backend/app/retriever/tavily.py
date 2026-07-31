import logging
import socket
from typing import Any

import httpx
import requests
from starlette.concurrency import run_in_threadpool
from tavily import TavilyClient

from app.core.config import Settings
from app.models.analysis import Evidence
from app.retriever.exceptions import (
    RetrievalConfigError,
    RetrievalError,
    RetrievalRateLimitError,
    RetrievalTimeoutError,
)

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if not settings.tavily_api_key:
            raise RetrievalConfigError("TAVILY_API_KEY is not configured")

        self._settings = settings
        self._client = client or TavilyClient(api_key=settings.tavily_api_key)

    async def retrieve(self, claim_text: str) -> list[Evidence]:
        normalized_claim = claim_text.strip()

        if not normalized_claim:
            return []

        try:
            response = await run_in_threadpool(self._search, normalized_claim)
        except (TimeoutError, socket.timeout, httpx.TimeoutException, requests.exceptions.Timeout) as exc:
            raise RetrievalTimeoutError("Tavily search timed out") from exc
        except Exception as exc:
            self._handle_tavily_error(exc)

        results = response.get("results", []) if isinstance(response, dict) else []
        evidence = [
            Evidence(
                title=str(result.get("title") or "Untitled source"),
                url=str(result.get("url") or ""),
                content=str(result.get("content") or result.get("raw_content") or ""),
            )
            for result in results[: self._settings.tavily_max_results]
            if isinstance(result, dict) and result.get("url") and (result.get("content") or result.get("raw_content"))
        ]

        logger.info(
            "Retrieved evidence",
            extra={"claim": normalized_claim, "evidence_count": len(evidence)},
        )

        return evidence

    def _search(self, claim_text: str) -> dict[str, Any]:
        return self._client.search(
            query=claim_text,
            search_depth=self._settings.tavily_search_depth,
            max_results=self._settings.tavily_max_results,
            include_answer=False,
            include_raw_content=False,
        )

    def _handle_tavily_error(self, exc: Exception) -> None:
        status_code = getattr(exc, "status_code", None) or getattr(exc, "status", None) or getattr(exc, "code", None)

        if str(status_code) == "429":
            raise RetrievalRateLimitError("Tavily rate limit exceeded") from exc

        raise RetrievalError("Tavily search failed") from exc
