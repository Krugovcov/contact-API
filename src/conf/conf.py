from pydantic import ConfigDict, field_validator

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://postgres:567234@localhost:5432/test_db"
    SECRET_KEY_JWT: str = "1234567890"
    ALGORITHM: str = "HS256"
    MAIL_USERNAME: str = "postmaster@localhost"
    MAIL_PASSWORD: str = "password"
    MAIL_FROM: str = "noreply@localhost"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.meta.ua"

    REDIS_DOMAIN: str = 'localhost'
    REDIS_PORT: 6379
    REDIS_PASSWORD: str = None

    CLD_NAME: str = "contacts"
    CLD_API_KEY: int = 552962473973189
    CLD_API_SECRET: str = "secret"

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v):
        if v not in ["HS256", "HS512"]:
            raise ValueError("ALGORITHM must be one of 'HS256' or 'HS512'")
        return v

    model_config = ConfigDict(extra='ignore', env_file=".env", env_file_encoding="utf-8")  # noqa


config = Settings()