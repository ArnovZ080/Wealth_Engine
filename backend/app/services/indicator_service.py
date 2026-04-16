"""
Indicator Service — Dumb Mode Technical Baseline.

Uses pandas-ta to evaluate RSI, SMA, MACD, BBands, and Volume.
Implements the recursive 30-day decision audit logic.
"""

import logging
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import pandas as pd
try:
    import pandas_ta as ta
except ImportError:
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
    confidence: float          # 0.0 to 1.0
    indicators: dict           # Individual indicator readings
    summary: str               # Human-readable explanation

class IndicatorService:
    """
    Runs Dumb Mode baseline technical analysis.
    """

    async def analyze(
        self,
        connector: BaseExchangeConnector,
        symbol: str,
        timeframe: str = "1h",
        lookback: int = 200
    ) -> IndicatorResult:
        """
        Fetch OHLCV data and run indicators.
        Returns a composite signal with confidence score.
        """
        try:
            raw_ohlcv = await connector.get_ohlcv(symbol, timeframe, limit=lookback)
            if not raw_ohlcv or len(raw_ohlcv) < 50:
                return self._neutral_result("Insufficient data points")

            df = pd.DataFrame(
                raw_ohlcv, 
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["close"] = pd.to_numeric(df["close"])
            df["volume"] = pd.to_numeric(df["volume"])

            votes = 0
            readings = {}

            # 1. RSI (14)
            rsi = df.ta.rsi(length=14)
            current_rsi = rsi.iloc[-1]
            readings["rsi"] = float(current_rsi)
            if current_rsi < 30:
                votes += 2 if current_rsi < 20 else 1
            elif current_rsi > 70:
                votes -= 2 if current_rsi > 80 else 1

            # 2. SMA Crossover (20/50)
            sma20 = df.ta.sma(length=20)
            sma50 = df.ta.sma(length=50)
            cur_20, prev_20 = sma20.iloc[-1], sma20.iloc[-2]
            cur_50, prev_50 = sma50.iloc[-1], sma50.iloc[-2]
            
            if prev_20 < prev_50 and cur_20 > cur_50:
                votes += 2 # Golden Cross
            elif prev_20 > prev_50 and cur_20 < cur_50:
                votes -= 2 # Death Cross
            readings["sma20"] = float(cur_20)
            readings["sma50"] = float(cur_50)

            # 3. MACD (12, 26, 9)
            macd_df = df.ta.macd(fast=12, slow=26, signal=9)
            # Columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
            macd_line = macd_df["MACD_12_26_9"]
            signal_line = macd_df["MACDs_12_26_9"]
            cur_m, prev_m = macd_line.iloc[-1], macd_line.iloc[-2]
            cur_s, prev_s = signal_line.iloc[-1], signal_line.iloc[-2]

            if prev_m < prev_s and cur_m > cur_s:
                votes += 1
            elif prev_m > prev_s and cur_m < cur_s:
                votes -= 1
            readings["macd"] = float(cur_m)

            # 4. Bollinger Bands (20, 2)
            bbands = df.ta.bbands(length=20, std=2)
            # Columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
            lower_band = bbands["BBL_20_2.0"].iloc[-1]
            upper_band = bbands["BBU_20_2.0"].iloc[-1]
            close = df["close"].iloc[-1]
            
            if close <= lower_band:
                votes += 1
            elif close >= upper_band:
                votes -= 1
            readings["bb_lower"] = float(lower_band)
            readings["bb_upper"] = float(upper_band)

            # 5. Volume Confirmation
            avg_vol = df["volume"].rolling(window=20).mean().iloc[-1]
            cur_vol = df["volume"].iloc[-1]
            high_vol = cur_vol > (avg_vol * 1.5)
            readings["volume_ratio"] = float(cur_vol / avg_vol)

            # Composite Scoring
            signal = self._map_votes_to_signal(votes)
            
            # Confidence Logic
            max_votes = 6 # (RSI 2, SMA 2, MACD 1, BB 1)
            base_confidence = min(abs(votes) / max_votes, 1.0)
            
            # Volume multiplier
            multiplier = 1.0 if high_vol else 0.75
            final_confidence = base_confidence * multiplier

            summary = f"Signal: {signal.value} (Votes: {votes}, VolRatio: {readings['volume_ratio']:.2f})"

            return IndicatorResult(
                signal=signal,
                confidence=final_confidence,
                indicators=readings,
                summary=summary
            )

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
        return IndicatorResult(
            signal=Signal.NEUTRAL,
            confidence=0.0,
            indicators={},
            summary=reason
        )
