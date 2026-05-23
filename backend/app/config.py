from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./data/alerts.db"
    poll_interval_seconds: int = 60
    discord_webhook_url: str = ""
    yahoo_user_agent: str = "stock_alert/0.1 (precious metals ratio alerts)"


settings = Settings()
Path("data").mkdir(parents=True, exist_ok=True)
