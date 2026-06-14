from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools.yfinance_tool import get_stock_data
from config.settings import settings
from config.prompts import TECHNICAL_SYSTEM
from utils.retry import groq_retry

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TECHNICAL_SYSTEM),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def _build_agent() -> AgentExecutor:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.1,
    )
    tools = [get_stock_data]
    agent = create_tool_calling_agent(llm, tools, _PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=3)


_executor = _build_agent()


@groq_retry
def analyze_technical(symbol: str) -> str:
    result = _executor.invoke({
        "input": f"วิเคราะห์ {symbol} แบบ technical analysis ให้ครบ บอก trend, RSI, MACD, volume และ recommendation"
    })
    return result["output"]
