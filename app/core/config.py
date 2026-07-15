from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="./data/.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/app.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    upload_dir: str = "./data/uploads"


settings = Settings()

