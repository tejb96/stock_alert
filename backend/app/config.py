from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./data/alerts.db"
    poll_interval_seconds: int = 60
    discord_webhook_url: str = ""
    yahoo_user_agent: str = "stock_alert/0.1 (precious metals ratio alerts)"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    apewisdom_enabled: bool = False
    apewisdom_fetch_interval_minutes: int = 60
    apewisdom_min_mentions: int = 20
    apewisdom_alert_mentions: int = 50
    apewisdom_alert_change_24h: float = 100.0
    apewisdom_alert_score_threshold: float = 150.0
    apewisdom_alert_cooldown_hours: int = 6
    apewisdom_alert_max_per_cycle: int = 3
    apewisdom_daily_summary_hour_utc: int = 21
    apewisdom_history_days: int = 60
    apewisdom_top_n: int = 50

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def apewisdom_fetch_interval_seconds(self) -> int:
        return self.apewisdom_fetch_interval_minutes * 60


settings = Settings()
Path("data").mkdir(parents=True, exist_ok=True)
