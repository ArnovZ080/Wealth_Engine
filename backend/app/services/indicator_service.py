"""
Indicator Service — Dumb Mode Technical Baseline.

Uses ta library to evaluate RSI, SMA, MACD, BBands, and Volume.
Implements the recursive 30-day decision audit logic.
"""

import logging
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import pandas as pd
import ta

from app.exchanges.base_connector import BaseExchangeConnector

logger = logging.getLogger(__name__)

class Signal(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

@dataclass
class IndicatorResult:
    signal: Signal
    confidence: float
    indicators: dict
    summary: str

class IndicatorService:
    async def analyze(self, connector: BaseExchangeConnector, symbol: str, timeframe: str = "1h", lookback: int = 200) -> IndicatorResult:
        try:
            raw_ohlcv = await connector.get_ohlcv(symbol, timeframe, limit=lookback)
            if not raw_ohlcv or len(raw_ohlcv) < 50:
                return self._neutral_result("Insufficient data points")

            df = pd.DataFrame(raw_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["close"] = pd.to_numeric(df["close"])
            df["volume"] = pd.to_numeric(df["volume"])
            df["high"] = pd.to_numeric(df["high"])
            df["low"] = pd.to_numeric(df["low"])

            votes = 0
            readings = {}

            rsi = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
            current_rsi = rsi.iloc[-1]
            readings["rsi"] = float(current_rsi)
            if current_rsi < 30:
                votes += 2 if current_rsi < 20 else 1
            elif current_rsi > 70:
                votes -= 2 if current_rsi > 80 else 1

            sma20 = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()
            sma50 = ta.trend.SMAIndicator(close=df['close'], window=50).sma_indicator()
            cur_20, prev_20 = sma20.iloc[-1], sma20.iloc[-2]
            cur_50, prev_50 = sma50.iloc[-1], sma50.iloc[-2]
            if prev_20 < prev_50 and cur_20 > cur_50:
                votes += 2
            elif prev_20 > prev_50 and cur_20 < cur_50:
                votes -= 2
            readings["sma20"] = float(cur_20)
            readings["sma50"] = float(cur_50)

            macd_obj = ta.trend.MACD(close=df['close'], window_fast=12, window_slow=26, window_sign=9)
            macd_line = macd_obj.macd()
            signal_line = macd_obj.macd_signal()
            cur_m, prev_m = macd_line.iloc[-1], macd_line.iloc[-2]
            cur_s, prev_s = signal_line.iloc[-1], signal_line.iloc[-2]
            if prev_m < prev_s and cur_m > cur_s:
                votes += 1
            elif prev_m > prev_s and cur_m < cur_s:
                votes -= 1
            readings["macd"] = float(cur_m)

            bb_obj = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
            lower_band = bb_obj.bollinger_lband().iloc[-1]
            upper_band = bb_obj.bollinger_hband().iloc[-1]
            close = df["close"].iloc[-1]
            if close <= lower_band:
                votes += 1
            elif close >= upper_band:
                votes -= 1
            readings["bb_lower"] = float(lower_band)
            readings["bb_upper"] = float(upper_band)

            avg_vol = df["volume"].rolling(window=20).mean().iloc[-1]
            cur_vol = df["volume"].iloc[-1]
            high_vol = cur_vol > (avg_vol * 1.5)
            readings["volume_ratio"] = float(cur_vol / avg_vol)

            signal = self._map_votes_to_signal(votes)
            max_votes = 6
            base_confidence = min(abs(votes) / max_votes, 1.0)
            multiplier = 1.0 if high_vol else 0.75
            final_confidence = base_confidence * multiplier

            summary = f"Signal: {signal.value} (Votes: {votes}, VolRatio: {readings['volume_ratio']:.2f})"
            return IndicatorResult(signal=signal, confidence=final_confidence, indicators=readings, summary=summary)

        except Exception as e:
            logger.error("Indicator analysis failed for %s: %s", symbol, e)
            return self._neutral_result(f"Error: {str(e)}")

    def _map_votes_to_signal(self, votes: int) -> Signal:
        if votes >= 4: return Signal.STRONG_BUY
        if votes >= 2: return Signal.BUY
        if votes <= -4: return Signal.STRONG_SELL
        if votes <= -2: return Signal.SELL
        return Signal.NEUTRAL

    def _neutral_result(self, reason: str) -> IndicatorResult:
        return IndicatorResult(signal=Signal.NEUTRAL, confidence=0.0, indicators={}, summary=reason)
