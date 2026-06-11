from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "APIS MVP"
    POSTGRES_USER: str = "apis"
    POSTGRES_PASSWORD: str = "apis_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5435"
    POSTGRES_DB: str = "apis_db"
    GEMINI_API_KEY: str = ""
    DATABASE_URL: Optional[str] = None

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()

