from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    anthropic_api_key: str = ""
    database_url: str = "postgresql+psycopg://garmentiq:garmentiq_dev@db:5432/garmentiq"
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 10
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_retries: int = 3


settings = Settings()
