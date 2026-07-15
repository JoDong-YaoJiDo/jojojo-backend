from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # model_config = SettingsConfigDict(env_file="./.env", env_file_encoding="utf-8", extra="ignore")
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )
    database_url: str = "sqlite:///./app.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    upload_dir: str = "./uploads"


settings = Settings()