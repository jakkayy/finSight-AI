import logging
from concurrent.futures import ThreadPoolExecutor, Future
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from agents.technical_agent import analyze_technical
from agents.news_agent import analyze_news
from agents.sentiment_agent import analyze_sentiment
from config.settings import settings
from config.prompts import ORCHESTRATOR_SUMMARY

logger = logging.getLogger(__name__)

_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ORCHESTRATOR_SUMMARY),
    ("human", "สรุปการวิเคราะห์ {symbol}"),
])

_FALLBACKS = {
    "technical": "ไม่สามารถดึงข้อมูล technical ได้",
    "news": "ไม่สามารถดึงข่าวได้",
    "sentiment": "ไม่สามารถวิเคราะห์ sentiment ได้",
}


def _resolve(future: Future, key: str) -> str:
    try:
        return future.result(timeout=90)
    except Exception as e:
        logger.warning("%s agent failed: %s", key, e)
        return _FALLBACKS[key]


def _summarize(symbol: str, technical: str, news: str, sentiment: str) -> str:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.2,
    )
    chain = _SUMMARY_PROMPT | llm
    response = chain.invoke({
        "symbol": symbol,
        "technical": technical,
        "news": news,
        "sentiment": sentiment,
    })
    return response.content


def run_full_analysis(symbol: str) -> str:
    symbol = symbol.upper()

    with ThreadPoolExecutor(max_workers=3) as executor:
        f_technical = executor.submit(analyze_technical, symbol)
        f_news = executor.submit(analyze_news, symbol)
        f_sentiment = executor.submit(analyze_sentiment, symbol)

        technical = _resolve(f_technical, "technical")
        news = _resolve(f_news, "news")
        sentiment = _resolve(f_sentiment, "sentiment")

    return _summarize(symbol, technical, news, sentiment)
