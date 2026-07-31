import pytest

from app.core.config import Settings
from app.retriever.tavily import Retriever


class FakeTavilyClient:
    def __init__(self, response: dict[str, object]) -> None:
        self._response = response

    def search(self, **_kwargs: object) -> dict[str, object]:
        return self._response


def make_settings() -> Settings:
    return Settings(TAVILY_API_KEY="test-key")


@pytest.mark.anyio
async def test_retriever_returns_top_five_evidence_items() -> None:
    client = FakeTavilyClient(
        {
            "results": [
                {"title": f"Title {index}", "url": f"https://example.com/{index}", "content": f"Content {index}"}
                for index in range(6)
            ]
        }
    )
    retriever = Retriever(settings=make_settings(), client=client)

    evidence = await retriever.retrieve("A factual claim")

    assert len(evidence) == 5
    assert evidence[0].title == "Title 0"
    assert evidence[0].url == "https://example.com/0"
    assert evidence[0].content == "Content 0"


@pytest.mark.anyio
async def test_retriever_handles_empty_search_results() -> None:
    retriever = Retriever(settings=make_settings(), client=FakeTavilyClient({"results": []}))

    assert await retriever.retrieve("A factual claim") == []
