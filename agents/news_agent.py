from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools.rss_tool import get_financial_news, get_thai_market_news
from tools.search_tool import web_search
from config.settings import settings
from config.prompts import NEWS_SYSTEM
from utils.retry import groq_retry

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", NEWS_SYSTEM),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def _build_agent() -> AgentExecutor:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.1,
    )
    tools = [get_financial_news, get_thai_market_news, web_search]
    agent = create_tool_calling_agent(llm, tools, _PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=4)


_executor = _build_agent()


@groq_retry
def analyze_news(symbol: str) -> str:
    result = _executor.invoke({
        "input": f"ดึงข่าวล่าสุดเกี่ยวกับ {symbol} และวิเคราะห์ว่ากระทบต่อราคาอย่างไร"
    })
    return result["output"]
