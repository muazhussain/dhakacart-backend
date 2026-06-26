"""Application configuration loaded from environment variables and .env file."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """All runtime configuration for the Dhakacart API.

    Attributes:
        app_name: API title shown in docs.
        debug: Enables debug mode and SQL query logging.
        database_url: PostgreSQL connection URL.
        redis_url: Redis connection URL.
        mongodb_url: MongoDB connection URL.
        mongodb_db: MongoDB database name.
        opensearch_url: OpenSearch host URL.
        jwt_secret_key: Secret key for JWT signing.
        jwt_algorithm: JWT signing algorithm.
        access_token_expire_minutes: Access token expiry duration in minutes.
        refresh_token_expire_days: Refresh token expiry duration in days.
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str
    debug: bool
    database_url: str
    redis_url: str
    mongodb_url: str
    mongodb_db: str
    opensearch_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


settings = Settings()  # type: ignore[call-arg]
