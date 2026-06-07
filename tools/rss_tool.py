import feedparser
from datetime import datetime, timezone
from langchain_core.tools import tool

_FEEDS = {
    "google_finance": "https://news.google.com/rss/search?q={symbol}+stock&hl=en&gl=US&ceid=US:en",
    "thairath": "https://www.thairath.co.th/rss/economic.xml",
    "krungthep_turakij": "https://www.krungthepturakij.com/rss/",
}


def _parse_feed(url: str, max_items: int = 5) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:max_items]:
        published = entry.get("published", "")
        items.append({
            "title": entry.get("title", ""),
            "summary": entry.get("summary", "")[:300],
            "link": entry.get("link", ""),
            "published": published,
        })
    return items


@tool
def get_financial_news(symbol: str, max_items: int = 5) -> list[dict]:
    """Fetch recent financial news for a stock symbol from Google News RSS.

    Args:
        symbol: Stock ticker symbol e.g. AAPL, NVDA
        max_items: Maximum number of news articles to return
    """
    url = _FEEDS["google_finance"].format(symbol=symbol)
    news = _parse_feed(url, max_items)
    return news if news else [{"title": f"No news found for {symbol}", "summary": "", "link": "", "published": ""}]


@tool
def get_thai_market_news(max_items: int = 5) -> list[dict]:
    """Fetch latest Thai financial market news from Krungthep Turakij RSS.

    Args:
        max_items: Maximum number of news articles to return
    """
    return _parse_feed(_FEEDS["krungthep_turakij"], max_items)
