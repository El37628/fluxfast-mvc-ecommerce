import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )

    NAME: str = "FluxFast MVC E-Commerce"
    ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecommerce_mvc.db"

    @property
    def is_debug(self) -> bool:
        return self.ENV.lower() in ("development", "test", "dev")


settings = Settings()

# Allow standard DATABASE_URL override if present without APP_ prefix
if "DATABASE_URL" in os.environ:
    settings.DATABASE_URL = os.environ["DATABASE_URL"]
