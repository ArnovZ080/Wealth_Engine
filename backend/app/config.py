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
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "fractal"
    db_password: str = "DudeGraffiti"
    db_name: str = "fractal_wealth"

    @property
    def database_url(self) -> str:
        from sqlalchemy.engine import URL
        url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name
        )
        return url.render_as_string(hide_password=False)

    @property
    def database_url_sync(self) -> str:
        from sqlalchemy.engine import URL
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name
        )
        return url.render_as_string(hide_password=False)

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

    # ── Phase 3A: Auth & Encryption ──────────────────────────────────────
    jwt_secret_key: str = "placeholder-secret-change-in-prod"
    master_email: str = "arno@example.com"
    credential_encryption_key: Optional[str] = None
    access_token_expire_minutes: int = 60 * 24 # 24 hours
    refresh_token_expire_days: int = 7

    # ── Waterfall Split Ratios ──────────────────────────────────────────
    # These are the canonical 15/20/50/15 splits from the Master Document §1.1
    waterfall_reservoir_pct: Decimal = Decimal("0.15")
    waterfall_nursery_pct: Decimal = Decimal("0.20")
    waterfall_vault_pct: Decimal = Decimal("0.50")
    waterfall_reinvestment_pct: Decimal = Decimal("0.15")

    # ── Defaults ────────────────────────────────────────────────────────
    default_tax_rate: Decimal = Decimal("0.30")
    default_tier2_capacity: Decimal = Decimal("50000.00000000")
    default_seed_value: Decimal = Decimal("1000.00000000")
    default_stop_loss_floor: Decimal = Decimal("850.00000000")
    nursery_seed_threshold: Decimal = Decimal("1000.00000000")

    base_currency: str = "ZAR"
    display_currency: str = "USD"

    # ── Heartbeat / Legacy Protocol ─────────────────────────────────────
    heartbeat_warning_days_1: int = 90
    heartbeat_warning_days_2: int = 150
    heartbeat_legacy_trigger_days: int = 180

    # ── Convenience Aliases ─────────────────────────────────────────────
    @property
    def tax_rate(self) -> Decimal:
        return self.default_tax_rate

    @property
    def vault_tier2_capacity(self) -> Decimal:
        return self.default_tier2_capacity


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — reads env once per process."""
    return Settings()
