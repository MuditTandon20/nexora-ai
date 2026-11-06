from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./nexora.db'
    environment: str = 'development'
    frontend_origin: str = 'http://localhost:3000'
    session_hours: int = 12
    storage_backend: str = 'local'
    upload_dir: str = './uploads'
    s3_bucket: str = ''
    s3_endpoint_url: str | None = None
    aws_region: str = 'ap-south-1'
    llm_base_url: str = ''
    llm_api_key: str = ''
    llm_model: str = ''
    llm_input_cost_per_million: float = 0
    llm_output_cost_per_million: float = 0
    ai_daily_limit: int = 20
    ai_enabled: bool = False


@lru_cache
def settings():
    return Settings()
