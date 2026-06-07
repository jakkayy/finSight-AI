from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools.reddit_tool import get_reddit_sentiment
from tools.search_tool import web_search
from config.settings import settings

_SYSTEM_PROMPT = """คุณเป็นผู้เชี่ยวชาญด้าน sentiment analysis สำหรับตลาดการเงิน

วิเคราะห์ความรู้สึกของนักลงทุนจากโซเชียลมีเดียและอินเตอร์เน็ต:
1. **Overall Sentiment**: Bullish 🟢 / Bearish 🔴 / Neutral ⚪ (พร้อม % ประมาณ)
2. **ประเด็นที่พูดถึงมากสุด**: top 3 topics
3. **Retail vs Institutional**: ความเห็นต่างกันไหม
4. **Risk signals**: มีสัญญาณ FOMO หรือ Panic ไหม
5. **สรุป**: ควรระวังอะไร

ตอบเป็นภาษาไทย กระชับและมี emoji ประกอบ"""

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
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
