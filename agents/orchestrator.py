import asyncio
import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
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


class AnalysisState(TypedDict):
    symbol: str
    technical: str
    news: str
    sentiment: str
    report: str
    errors: Annotated[list, "append"]


def node_technical(state: AnalysisState) -> dict:
    try:
        return {"technical": analyze_technical(state["symbol"])}
    except Exception as e:
        logger.warning("Technical agent failed: %s", e)
        return {"technical": "ไม่สามารถดึงข้อมูล technical ได้", "errors": [str(e)]}


def node_news(state: AnalysisState) -> dict:
    try:
        return {"news": analyze_news(state["symbol"])}
    except Exception as e:
        logger.warning("News agent failed: %s", e)
        return {"news": "ไม่สามารถดึงข่าวได้", "errors": [str(e)]}


def node_sentiment(state: AnalysisState) -> dict:
    try:
        return {"sentiment": analyze_sentiment(state["symbol"])}
    except Exception as e:
        logger.warning("Sentiment agent failed: %s", e)
        return {"sentiment": "ไม่สามารถวิเคราะห์ sentiment ได้", "errors": [str(e)]}


def node_summarize(state: AnalysisState) -> dict:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.2,
    )
    chain = _SUMMARY_PROMPT | llm
    response = chain.invoke({
        "symbol": state["symbol"],
        "technical": state["technical"],
        "news": state["news"],
        "sentiment": state["sentiment"],
    })
    return {"report": response.content}


def build_graph() -> StateGraph:
    graph = StateGraph(AnalysisState)
    graph.add_node("technical", node_technical)
    graph.add_node("news", node_news)
    graph.add_node("sentiment", node_sentiment)
    graph.add_node("summarize", node_summarize)

    graph.set_entry_point("technical")
    graph.add_edge("technical", "news")
    graph.add_edge("news", "sentiment")
    graph.add_edge("sentiment", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


_graph = build_graph()


def run_full_analysis(symbol: str) -> str:
    symbol = symbol.upper()
    result = _graph.invoke({
        "symbol": symbol,
        "technical": "",
        "news": "",
        "sentiment": "",
        "report": "",
        "errors": [],
    })
    return result["report"]
