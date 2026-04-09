"""
Application configuration via pydantic-settings.

Environment variables are loaded from .env files and can be overridden
by actual environment variables (e.g., in Docker or CI).
"""

from typing import Optional
from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the Fractal Wealth Engine.

    All monetary defaults use Decimal strings to avoid float contamination.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── PostgreSQL ──────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://fractal:dev_password_change_me@localhost:5432/fractal_wealth"
    )
    database_url_sync: str = (
        "postgresql+psycopg2://fractal:dev_password_change_me@localhost:5432/fractal_wealth"
    )

    # ── Application ─────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    app_title: str = "Recursive Fractal Wealth Engine"
    app_version: str = "0.1.0"

    # ── AI Agents ───────────────────────────────────────────────────────
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.1-pro"
    anthropic_model: str = "claude-4.6-opus"
    
    max_refinement_rounds: int = 3
    alpha_hunter_confidence_threshold: int = 85

    # ── Waterfall Split Ratios ──────────────────────────────────────────
    # These are the canonical 15/20/50/15 splits from the Master Document §1.1
    waterfall_reservoir_pct: Decimal = Decimal("0.15")
    waterfall_nursery_pct: Decimal = Decimal("0.20")
    waterfall_vault_pct: Decimal = Decimal("0.50")
    waterfall_reinvestment_pct: Decimal = Decimal("0.15")

    # ── Defaults ────────────────────────────────────────────────────────
    default_tax_rate: Decimal = Decimal("0.30")
    default_tier2_capacity: Decimal = Decimal("50000.00000000")
    default_seed_value: Decimal = Decimal("100.00000000")
    default_stop_loss_floor: Decimal = Decimal("85.00000000")
    nursery_seed_threshold: Decimal = Decimal("100.00000000")

    # ── Heartbeat / Legacy Protocol ─────────────────────────────────────
    heartbeat_warning_days_1: int = 90
    heartbeat_warning_days_2: int = 150
    heartbeat_legacy_trigger_days: int = 180


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — reads env once per process."""
    return Settings()
