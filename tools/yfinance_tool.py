import yfinance as yf
import pandas as pd
from langchain_core.tools import tool


def _calc_rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2)


def _calc_macd(close: pd.Series):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return round(float(macd.iloc[-1]), 4), round(float(signal.iloc[-1]), 4)


@tool
def get_stock_data(symbol: str, period: str = "3mo") -> dict:
    """Fetch stock price data and compute RSI, EMA, MACD for a given symbol.

    Args:
        symbol: Stock ticker symbol e.g. AAPL, NVDA, BTC-USD
        period: yfinance period string e.g. 1mo, 3mo, 6mo, 1y
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)

    if hist.empty:
        return {"error": f"No data found for symbol: {symbol}"}

    close = hist["Close"]
    current = float(close.iloc[-1])
    prev = float(close.iloc[-2])

    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    macd, macd_signal = _calc_macd(close)

    high_52w = float(hist["High"].tail(252).max())
    low_52w = float(hist["Low"].tail(252).min())

    return {
        "symbol": symbol.upper(),
        "current_price": round(current, 2),
        "change_pct": round(((current - prev) / prev) * 100, 2),
        "rsi_14": _calc_rsi(close),
        "ema_20": round(ema20, 2),
        "ema_50": round(ema50, 2),
        "macd": macd,
        "macd_signal": macd_signal,
        "volume": int(hist["Volume"].iloc[-1]),
        "52w_high": round(high_52w, 2),
        "52w_low": round(low_52w, 2),
    }
