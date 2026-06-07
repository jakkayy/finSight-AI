from duckduckgo_search import DDGS
from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web for financial news and information using DuckDuckGo.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
    """
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return [
        {"title": r.get("title", ""), "body": r.get("body", "")[:400], "href": r.get("href", "")}
        for r in results
    ]
