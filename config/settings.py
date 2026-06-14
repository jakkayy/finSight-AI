from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    telegram_bot_token: str

    database_url: str = "postgresql://finsight:finsight@postgres:5432/finsight"
    redis_url: str = "redis://redis:6379"

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "FinSight/1.0"

    class Config:
        env_file = ".env"


settings = Settings()
