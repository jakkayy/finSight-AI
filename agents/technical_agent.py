from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools.yfinance_tool import get_stock_data
from config.settings import settings

_SYSTEM_PROMPT = """คุณเป็น technical analyst ผู้เชี่ยวชาญด้านการวิเคราะห์หุ้นและสินทรัพย์ทางการเงิน

เมื่อวิเคราะห์ให้ระบุ:
1. **แนวโน้ม (Trend)**: ราคาเทียบกับ EMA20 และ EMA50
2. **Momentum**: RSI (>70 overbought, <30 oversold) และ MACD crossover
3. **Volume**: ปริมาณซื้อขายผิดปกติหรือไม่
4. **สรุป**: Bullish / Bearish / Neutral พร้อมเหตุผล

ตอบเป็นภาษาไทย กระชับ ชัดเจน และ actionable"""

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
    tools = [get_stock_data]
    agent = create_tool_calling_agent(llm, tools, _PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=3)


_executor = _build_agent()


def analyze_technical(symbol: str) -> str:
    result = _executor.invoke({
        "input": f"วิเคราะห์ {symbol} แบบ technical analysis ให้ครบ บอก trend, RSI, MACD, volume และ recommendation"
    })
    return result["output"]
