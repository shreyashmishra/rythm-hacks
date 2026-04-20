from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = 4000
    database_url: str
    jwt_secret: str
    cookie_name: str = "rythm_session"
    cors_origin: str = "http://localhost:5173"
    cookie_secure: bool = False
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("JWT_SECRET must be at least 8 characters")
        return value

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("mysql://"):
            return self.database_url.replace("mysql://", "mysql+pymysql://", 1)
        return self.database_url


settings = Settings()
