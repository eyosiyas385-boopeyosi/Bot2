import asyncio
import os
import time
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .strategy import analyze_pair
from .dashboard import HTML

app = FastAPI(title="Hybrid Statistical Arbitrage Bot", version="1.0.0")
STARTED = time.time()
LAST_ANALYSIS = None
LAST_ERROR = None
LATEST = None
TASK = None

TICKERS = {"AUDUSD": "AUDUSD=X", "NZDUSD": "NZDUSD=X"}


def fetch_prices(period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    raw = yf.download(
        list(TICKERS.values()),
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    if raw is None or raw.empty:
        raise RuntimeError("No candles received from Yahoo Finance. Try later or use a broker data feed.")

    columns = {}
    for symbol, ticker in TICKERS.items():
        if isinstance(raw.columns, pd.MultiIndex):
            if ticker in raw.columns.get_level_values(0):
                columns[symbol] = raw[ticker]["Close"]
            elif ticker in raw.columns.get_level_values(-1):
                columns[symbol] = raw.xs(ticker, axis=1, level=-1)["Close"]
            else:
                raise RuntimeError(f"Ticker data missing: {ticker}")
        else:
            raise RuntimeError("Unexpected market-data column format.")
    frame = pd.DataFrame(columns).dropna()
    if len(frame) < 180:
        raise RuntimeError(f"Not enough synchronized 5-minute bars: {len(frame)}.")
    return frame


async def run_analysis():
    global LAST_ANALYSIS, LAST_ERROR, LATEST
    try:
        prices = await asyncio.to_thread(fetch_prices)
        result = await asyncio.to_thread(analyze_pair, prices)
        LATEST = result
        LAST_ANALYSIS = datetime.now(timezone.utc).isoformat()
        LAST_ERROR = None
    except Exception as exc:
        LAST_ERROR = str(exc)


async def analysis_loop():
    while True:
        await run_analysis()
        await asyncio.sleep(300)


@app.on_event("startup")
async def startup():
    global TASK
    if os.getenv("ENABLE_BACKGROUND_ANALYSIS", "true").lower() == "true":
        TASK = asyncio.create_task(analysis_loop())


@app.on_event("shutdown")
async def shutdown():
    if TASK:
        TASK.cancel()


@app.get("/health")
def health():
    return {"status": "ok", "mode": "signal-only"}


@app.get("/api/status")
def status():
    return {
        "service": "Hybrid Statistical Arbitrage Bot",
        "mode": "SIGNAL ONLY — NO BROKER ORDERS",
        "uptime_seconds": int(time.time() - STARTED),
        "last_analysis": LAST_ANALYSIS,
        "last_error": LAST_ERROR,
        "latest": LATEST,
        "automatic_live_orders": False,
    }


@app.post("/api/analyze")
async def analyze_now():
    await run_analysis()
    if LAST_ERROR:
        raise HTTPException(status_code=503, detail=LAST_ERROR)
    return LATEST


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTML
