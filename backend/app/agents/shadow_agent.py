"""
Shadow Agent — Claude 4.6 Opus.

Focus: Adversarial Review, Veto logic, and Risk verification.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import anthropic

from app.agents.base import BaseAgent
from app.agents.alpha_hunter import TradeMemo

logger = logging.getLogger(__name__)

class ShadowVerdict(BaseModel):
    """
    The verdict from the Shadow Agent.
    """
    decision: str = Field(..., pattern="^(APPROVE|VETO|REFINE)$")
    flaws_found: List[str] = []
    risk_assessment: str
    suggested_adjustments: Optional[Dict[str, Any]] = None
    confidence_in_veto: int = Field(..., ge=0, le=100)
    reasoning: str

class ShadowAgent(BaseAgent):
    """
    Claude Implementation.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "claude-3-opus-20240229"):
        super().__init__("Shadow Agent")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model_name = model_name
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    async def review_proposal(self, memo: TradeMemo) -> ShadowVerdict:
        """
        Adversarial review (Master Document §4.2).
        """
        if not self.client:
            logger.warning("No Anthropic API key found. Falling back to mock.")
            return self._mock_review(memo)

        try:
            prompt = self._build_shadow_prompt(memo)
            
            # Call Claude
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return self._parse_shadow_response(response.content[0].text)
        except Exception as e:
            logger.error("Claude API call failed: %s. Falling back.", e)
            return self._mock_review(memo)

    def _build_shadow_prompt(self, memo: TradeMemo) -> str:
        return f"""
        You are the 'Shadow Agent', the adversarial risk auditor for the Recursive Fractal Wealth Engine.
        Your sole mission is to find reasons this trade should NOT be executed. You are the skeptic.

        PROPOSED TRADE (Alpha Hunter):
        Ticker: {memo.ticker}
        Direction: {memo.direction}
        Entry: {memo.entry_price}
        Target: {memo.target_exit}
        Stop Loss: {memo.stop_loss}
        Size: {memo.position_size}
        Rationale: {memo.rationale}

        AUDIT FOCUS:
        1. Liquidity risk: Is the ticker liquid enough for this size?
        2. Ground Zero adequacy: Does the stop loss leave enough buffer before the $85 seed floor?
        3. Logic flaws: Is the Hunter's rationale truly sound or just pattern-matching noise?

        OUTPUT FORMAT:
        Output ONLY valid JSON matching this schema:
        {{
            "decision": "APPROVE|VETO|REFINE",
            "flaws_found": ["list of strings"],
            "risk_assessment": "concise summary",
            "suggested_adjustments": {{ "field": "value" }} or null,
            "confidence_in_veto": number (0-100),
            "reasoning": "adversarial breakdown"
        }}
        """

    def _parse_shadow_response(self, text: str) -> ShadowVerdict:
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(clean_text)
        return ShadowVerdict(**data)

    def _mock_review(self, memo: TradeMemo) -> ShadowVerdict:
        # Mock logic
        risk_pct = abs(memo.entry_price - memo.stop_loss) / memo.entry_price
        if risk_pct > 0.05:
            return ShadowVerdict(
                decision="REFINE",
                flaws_found=["Stop loss too wide (fallback)."],
                risk_assessment="High risk of Ground Zero event.",
                confidence_in_veto=80,
                reasoning="Mocked adversarial response."
            )
        return ShadowVerdict(
            decision="APPROVE",
            risk_assessment="Risk parameters within acceptable variance.",
            confidence_in_veto=10,
            reasoning="Mocked adversarial approval."
        )

    async def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Any:
        if not self.client:
            return "Mock response: Anthropic API key missing."
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
