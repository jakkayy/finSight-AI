import praw
from langchain_core.tools import tool
from config.settings import settings

_reddit = None


def _get_reddit() -> praw.Reddit:
    global _reddit
    if _reddit is None:
        _reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
    return _reddit


@tool
def get_reddit_sentiment(symbol: str, subreddits: str = "wallstreetbets+investing+stocks", limit: int = 10) -> list[dict]:
    """Fetch recent Reddit posts mentioning a stock symbol for sentiment analysis.

    Args:
        symbol: Stock ticker symbol e.g. AAPL, NVDA
        subreddits: Plus-separated list of subreddits to search
        limit: Number of posts to fetch per subreddit
    """
    reddit = _get_reddit()
    posts = []
    for sub_name in subreddits.split("+"):
        try:
            sub = reddit.subreddit(sub_name)
            for post in sub.search(symbol, limit=limit, sort="new", time_filter="week"):
                posts.append({
                    "subreddit": sub_name,
                    "title": post.title,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "selftext": post.selftext[:300],
                    "url": f"https://reddit.com{post.permalink}",
                })
        except Exception:
            continue
    return posts
