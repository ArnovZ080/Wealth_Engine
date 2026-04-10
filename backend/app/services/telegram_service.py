"""
Telegram Service — Real-time notifications for trade events and system alerts.

Matches Master Document §12.2.
"""

import logging
import httpx
from typing import Optional
from app.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

class TelegramService:
    """
    Sends bot notifications to users and the master.
    """

    def __init__(self):
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.master_chat_id = getattr(settings, "TELEGRAM_MASTER_CHAT_ID", None)
        self.enabled = bool(self.bot_token)

    async def send_message(self, chat_id: str, text: str):
        """
        Send a message via Telegram Bot API.
        """
        if not self.enabled or not chat_id:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                if response.status_code != 200:
                    logger.error("Telegram API Error: %s %s", response.status_code, response.text)
        except Exception as e:
            logger.error("Failed to send Telegram message: %s", e)

    async def notify_master(self, text: str):
        """
        Send heartbeat or system-wide alerts to the master operator.
        """
        if self.master_chat_id:
            await self.send_message(self.master_chat_id, f"<b>[MASTER ALERT]</b>\n{text}")

    async def notify_user(self, user: User, text: str):
        """
        Send a private notification to a user if they have linked their chat id.
        """
        if user.telegram_chat_id:
            await self.send_message(user.telegram_chat_id, f"<b>[WE ENGINE]</b>\n{text}")
        
        # Always CC master for critical events (optional, but good for auditing)
        if self.master_chat_id:
            await self.send_message(self.master_chat_id, f"<b>[USER NOTIFY: {user.display_name}]</b>\n{text}")

    def format_trade_alert(self, trade_type: str, ticker: str, price: float, pnl: Optional[float] = None, reason: str = "") -> str:
        """Helper to format standardized trade alerts."""
        if trade_type.upper() == "BUY":
            return f"🟢 <b>BUY {ticker}</b>\nPrice: ${price:,.2f}\nReason: {reason}"
        elif trade_type.upper() == "SELL":
            emoji = "💰" if (pnl or 0) >= 0 else "🔴"
            pnl_str = f"P&L: <b>${pnl:,.2f}</b>" if pnl is not None else ""
            return f"{emoji} <b>SELL {ticker}</b>\nPrice: ${price:,.2f}\n{pnl_str}\nExit: {reason}"
        return f"Trade Update: {ticker} @ {price}"
