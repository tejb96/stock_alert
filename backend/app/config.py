from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./data/alerts.db"
    poll_interval_seconds: int = 60
    discord_webhook_url: str = ""
    yahoo_user_agent: str = "stock_alert/0.1 (precious metals ratio alerts)"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
Path("data").mkdir(parents=True, exist_ok=True)
