from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

BINANCE_BASE_URL = "https://api.binance.com"
SUPPORTED_INTERVALS = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}


class PredictRequest(BaseModel):
    symbol: str
    timeframe: Literal["1m", "5m", "15m", "1h", "4h", "1d"] = "1h"


class Prediction(BaseModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    signal: Literal["BUY", "SELL"]
    entry: float
    take_profit: float
    stop_loss: float
    confidence: float
    short_sma: float
    long_sma: float
    rsi: float
    atr: float


app = FastAPI(title="Crypto Predictor")


def _fetch_candles(symbol: str, interval: str, limit: int = 200) -> list[dict]:
    response = requests.get(
        f"{BINANCE_BASE_URL}/api/v3/klines",
        params={"symbol": symbol.upper(), "interval": interval, "limit": limit},
        timeout=10,
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Binance API error {response.status_code}: {response.text}",
        )

    return [
        {
            "open_time": int(item[0]),
            "open": float(item[1]),
            "high": float(item[2]),
            "low": float(item[3]),
            "close": float(item[4]),
            "volume": float(item[5]),
        }
        for item in response.json()
    ]


def _sma(values: list[float], period: int) -> float:
    if len(values) < period:
        raise HTTPException(status_code=400, detail=f"Not enough data for SMA{period}")
    return sum(values[-period:]) / period


def _rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        raise HTTPException(status_code=400, detail="Not enough data for RSI")

    gains = []
    losses = []
    for prev, curr in zip(closes[-period - 1 : -1], closes[-period:]):
        change = curr - prev
        if change >= 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-change)

    average_gain = sum(gains) / period
    average_loss = sum(losses) / period
    if average_loss == 0:
        return 100.0
    rs = average_gain / average_loss
    return 100 - (100 / (1 + rs))


def _atr(candles: list[dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        raise HTTPException(status_code=400, detail="Not enough data for ATR")

    trs = []
    for prev, curr in zip(candles[-period - 1 : -1], candles[-period:]):
        high = curr["high"]
        low = curr["low"]
        prev_close = prev["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)

    return sum(trs) / period


@app.post("/predict", response_model=Prediction)
def predict(body: PredictRequest) -> Prediction:
    interval = SUPPORTED_INTERVALS[body.timeframe]
    candles = _fetch_candles(body.symbol, interval)
    closes = [c["close"] for c in candles]

    short_sma = _sma(closes, 20)
    long_sma = _sma(closes, 50)
    rsi_value = _rsi(closes)
    atr_value = _atr(candles)

    price = closes[-1]
    is_bullish = short_sma > long_sma and rsi_value > 50
    signal: Literal["BUY", "SELL"] = "BUY" if is_bullish else "SELL"

    atr_multiplier = 1.8
    if signal == "BUY":
        entry = price
        take_profit = entry + atr_multiplier * atr_value
        stop_loss = entry - atr_value
    else:
        entry = price
        take_profit = entry - atr_multiplier * atr_value
        stop_loss = entry + atr_value

    confidence = min(max(abs(short_sma - long_sma) / price, 0.1), 0.9)

    return Prediction(
        symbol=body.symbol.upper(),
        timeframe=body.timeframe,
        timestamp=datetime.now(timezone.utc),
        signal=signal,
        entry=round(entry, 2),
        take_profit=round(take_profit, 2),
        stop_loss=round(stop_loss, 2),
        confidence=round(confidence, 2),
        short_sma=round(short_sma, 2),
        long_sma=round(long_sma, 2),
        rsi=round(rsi_value, 2),
        atr=round(atr_value, 2),
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Crypto predictor ready",
        "usage": "POST /predict with JSON {symbol, timeframe}",
    }
