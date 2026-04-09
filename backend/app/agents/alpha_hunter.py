"""
Alpha Hunter Agent — Gemini 3.1 Pro.

Focus: Multi-stage Bayesian Decision Funnel & Trade Proposal generation.
"""

import logging
import os
import json
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import google.generativeai as genai

from app.agents.base import BaseAgent, LLMResponse

logger = logging.getLogger(__name__)

class TradeMemo(BaseModel):
    """
    The canonical output of the Alpha Hunter.
    """
    seed_id: str
    ticker: str
    direction: str = Field(..., pattern="^(long|short)$")
    entry_price: Decimal
    target_exit: Decimal
    stop_loss: Decimal
    position_size: Decimal
    rationale: str
    confidence: int = Field(..., ge=0, le=100)
    strategy_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlphaHunter(BaseAgent):
    """
    Gemini Implementation. (Instruction specifies Gemini 3.1 Pro, using gemini-1.5-pro as stable target)
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-pro"):
        super().__init__("Alpha Hunter")
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model_name = model_name
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(model_name)
            except Exception as e:
                logger.error("Failed to initialize Gemini model: %s", e)
                self.model = None
        else:
            self.model = None

    async def generate_proposal(self, market_data: Dict[str, Any], seed_context: Dict[str, Any]) -> TradeMemo:
        """
        Call Gemini API with market data and seed context.
        """
        if not self.model:
            logger.warning("No Gemini API key found. Falling back to mock.")
            return self._mock_proposal(market_data, seed_context)

        try:
            prompt = self._build_hunter_prompt(market_data, seed_context)
            # Fetch response
            response = self.model.generate_content(prompt)
            return self._parse_hunter_response(response.text, market_data, seed_context)
        except Exception as e:
            logger.error("Gemini API call failed: %s. Falling back.", e)
            return self._mock_proposal(market_data, seed_context)

    def _build_hunter_prompt(self, market_data: Dict, seed_context: Dict) -> str:
        return f"""
        You are the 'Alpha Hunter', the primary trading intelligence for the Recursive Fractal Wealth Engine.
        Your goal is to propose a high-probability trade for a specific 'Seed' ($100 atomic unit).

        MARKET DATA:
        Ticker: {market_data.get('ticker')}
        Current Price: {market_data.get('current_price')}
        Indicators: {market_data.get('indicators')}
        Baseline Signal: {market_data.get('dumb_mode_signal')}

        SEED CONTEXT:
        Seed ID: {seed_context.get('seed_id')}
        Current Value: ${seed_context.get('current_value')}
        Stage: {seed_context.get('stage')}
        Strategy: {seed_context.get('strategy')}

        RISK GUARDRAILS:
        1. Never propose a stop-loss wider than 5% from entry.
        2. Never propose a position size exceeding 10% of seed value.
        3. Prioritize 'long' for Stage 1 seeds.

        OUTPUT FORMAT:
        Output ONLY valid JSON matching this schema:
        {{
            "ticker": "string",
            "direction": "long|short",
            "entry_price": number,
            "target_exit": number,
            "stop_loss": number,
            "position_size": number,
            "rationale": "detailed string",
            "confidence": number (0-100),
            "strategy_type": "string"
        }}
        """

    def _parse_hunter_response(self, text: str, market_data: Dict, seed_context: Dict) -> TradeMemo:
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(clean_text)
        return TradeMemo(
            seed_id=seed_context.get("seed_id", "unknown"),
            ticker=data["ticker"],
            direction=data["direction"],
            entry_price=Decimal(str(data["entry_price"])),
            target_exit=Decimal(str(data["target_exit"])),
            stop_loss=Decimal(str(data["stop_loss"])),
            position_size=Decimal(str(data["position_size"])),
            rationale=data["rationale"],
            confidence=int(data["confidence"]),
            strategy_type=data["strategy_type"]
        )

    def _mock_proposal(self, market_data: Dict, seed_context: Dict) -> TradeMemo:
        seed_value = Decimal(str(seed_context.get("current_value", 100)))
        pos_size = seed_value * Decimal("0.10")
        price = Decimal(str(market_data.get("current_price", 60000)))
        return TradeMemo(
            seed_id=seed_context.get("seed_id", "mock"),
            ticker=market_data.get("ticker", "BTC/USDT"),
            direction="long",
            entry_price=price,
            target_exit=price * Decimal("1.05"),
            stop_loss=price * Decimal("0.98"),
            position_size=pos_size,
            rationale="Mocked bullish proposal (Baseline fallback).",
            confidence=75,
            strategy_type="momentum"
        )

    async def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Any:
        if not self.model:
            return "Mock response: Gemini API key missing."
        response = self.model.generate_content(prompt)
        return response.text
