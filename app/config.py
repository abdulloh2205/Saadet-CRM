# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: str = Field(default="CHANGE_ME", alias="BOT_TOKEN")
    webapp_url: str = Field(default="http://localhost:8000/webapp", alias="WEBAPP_URL")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./toystore.db", alias="DATABASE_URL"
    )
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    admin_chat_id: int = Field(default=0, alias="ADMIN_CHAT_ID")

    # Business constants
    uchtepa_capacity: int = 100


settings = Settings()
