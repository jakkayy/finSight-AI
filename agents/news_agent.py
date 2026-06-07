from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools.rss_tool import get_financial_news, get_thai_market_news
from tools.search_tool import web_search
from config.settings import settings

_SYSTEM_PROMPT = """คุณเป็นนักวิเคราะห์ข่าวการเงิน ทำหน้าที่ดึงและวิเคราะห์ข่าวที่กระทบต่อราคาหุ้น

เมื่อวิเคราะห์ข่าวให้:
1. สรุปข่าวสำคัญ 3-5 ข้อ
2. ระบุ impact ต่อราคาหุ้น (+/- และเหตุผล)
3. บอกว่าข่าวนี้ระยะสั้น หรือ ระยะยาว
4. สรุป sentiment: Positive / Negative / Neutral

ตอบเป็นภาษาไทย กระชับและ actionable"""

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def _build_agent() -> AgentExecutor:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=settings.groq_api_key,
        temperature=0.1,
    )
    tools = [get_financial_news, get_thai_market_news, web_search]
    agent = create_tool_calling_agent(llm, tools, _PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=4)


_executor = _build_agent()


def analyze_news(symbol: str) -> str:
    result = _executor.invoke({
        "input": f"ดึงข่าวล่าสุดเกี่ยวกับ {symbol} และวิเคราะห์ว่ากระทบต่อราคาอย่างไร"
    })
    return result["output"]
