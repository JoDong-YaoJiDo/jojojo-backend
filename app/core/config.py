from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    upload_dir: str = "./uploads"
    tourism_json_path: str = "./tourism.json"


settings = Settings()

