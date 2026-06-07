# FinSight — Multi-Agent Investment Research

ระบบวิเคราะห์การลงทุนอัตโนมัติด้วย AI หลายตัวทำงานร่วมกัน ส่งรายงานผ่าน Telegram

## Architecture

```
User (Telegram)
      ↓
Orchestrator Agent (Groq Llama 70B)
 ↙            ↓            ↘
News        Technical     Sentiment
Agent        Agent          Agent
(RSS/DDG)  (yfinance)    (Reddit PRAW)
    ↘            ↓         ↙
        PostgreSQL + Redis
              ↓
    Daily Report (Telegram)
```

## Features

- **Multi-Agent Analysis** — Technical, News, Sentiment วิเคราะห์แยกกัน แล้วสรุปรวม
- **Morning Briefing** — ส่งรายงานอัตโนมัติทุกวัน 08:00 น.
- **Price Alerts** — แจ้งเตือนทันทีเมื่อราคาเกิน threshold
- **Watchlist** — ตั้ง watchlist และ alert ต่อ symbol ได้เลย
- **Free Stack** — ใช้ Groq (free tier) ทั้งหมด ไม่มีค่าใช้จ่าย

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Groq — Llama 3.3 70B / Llama 3.1 8B |
| Agent Framework | LangGraph + LangChain |
| Data — Price | yfinance |
| Data — News | Google News RSS, Krungthep Turakij RSS |
| Data — Sentiment | Reddit PRAW, DuckDuckGo |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL (Docker) |
| Cache | Redis (Docker) |
| Notification | Telegram Bot |
| Scheduler | APScheduler |

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | เริ่มต้นใช้งาน |
| `/analyze <symbol>` | Technical analysis (เร็ว) |
| `/report <symbol>` | Full report — Technical + News + Sentiment |
| `/add <symbol>` | เพิ่มใน watchlist |
| `/remove <symbol>` | ลบจาก watchlist |
| `/list` | ดู watchlist |
| `/alert <symbol> <n>` | ตั้ง alert เมื่อราคาเปลี่ยน n% |

ตัวอย่าง: `/report NVDA` หรือ `/alert BTC-USD 3`

## Getting Started

### 1. Clone & Setup

```bash
git clone <repo-url>
cd finSight
cp .env.example .env
```

### 2. ตั้งค่า `.env`

```env
GROQ_API_KEY=...        # จาก console.groq.com (ฟรี)
TELEGRAM_BOT_TOKEN=...  # จาก @BotFather
TELEGRAM_CHAT_ID=...    # Chat ID ของคุณ

# Optional — สำหรับ Sentiment Agent
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

### 3. รัน

```bash
# Start database
docker-compose up -d postgres redis

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

หรือรันทั้ง stack ด้วย Docker:

```bash
docker-compose up
```

## Project Structure

```
finSight/
├── agents/
│   ├── orchestrator.py      # LangGraph pipeline
│   ├── technical_agent.py   # RSI, EMA, MACD analysis
│   ├── news_agent.py        # News impact analysis
│   └── sentiment_agent.py   # Reddit/web sentiment
├── tools/
│   ├── yfinance_tool.py     # Stock price + indicators
│   ├── rss_tool.py          # RSS feed parser
│   ├── search_tool.py       # DuckDuckGo search
│   └── reddit_tool.py       # Reddit PRAW
├── bot/
│   └── telegram_bot.py      # Telegram command handlers
├── scheduler/
│   ├── jobs.py              # Morning briefing job
│   └── alert_jobs.py        # Price alert job
├── db/
│   ├── database.py          # SQLAlchemy engine + session
│   └── models.py            # User, Watchlist, AnalysisHistory
├── config/
│   ├── settings.py          # Pydantic settings
│   └── prompts.py           # All agent prompts
├── utils/
│   ├── logger.py            # Logging config
│   └── retry.py             # Tenacity retry decorator
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── main.py
```

## API Keys ที่ต้องใช้

| Service | ลงทะเบียนที่ | ราคา |
|---------|------------|------|
| Groq | [console.groq.com](https://console.groq.com) | ฟรี |
| Telegram Bot | @BotFather ใน Telegram | ฟรี |
| Reddit API | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) | ฟรี |

## ข้อจำกัด

- **Groq free tier**: ~14,400 req/day — เพียงพอสำหรับใช้ส่วนตัว
- **yfinance**: ข้อมูลหุ้นไทย (SET) อาจไม่ครบ
- **/report ใช้เวลา 30-90 วินาที** เพราะเรียก 3 agents ต่อเนื่องกัน

---

> ⚠️ ข้อมูลจาก FinSight เพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำการลงทุน
