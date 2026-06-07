from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools.reddit_tool import get_reddit_sentiment
from tools.search_tool import web_search
from config.settings import settings
from config.prompts import SENTIMENT_SYSTEM

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SENTIMENT_SYSTEM),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def _build_agent() -> AgentExecutor:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=settings.groq_api_key,
        temperature=0.2,
    )
    tools = [get_reddit_sentiment, web_search]
    agent = create_tool_calling_agent(llm, tools, _PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=4)


_executor = _build_agent()


def analyze_sentiment(symbol: str) -> str:
    result = _executor.invoke({
        "input": f"วิเคราะห์ sentiment ของนักลงทุนใน Reddit และอินเตอร์เน็ตสำหรับ {symbol} ในสัปดาห์นี้"
    })
    return result["output"]
