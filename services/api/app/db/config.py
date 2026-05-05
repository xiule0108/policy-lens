from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://policylens:policylens@localhost:5432/policylens",
        alias="DATABASE_URL",
    )
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    storage_dir: str = Field(default="./storage", alias="STORAGE_DIR")
    default_model_profile: str = Field(default="china_balanced", alias="DEFAULT_MODEL_PROFILE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url


settings = Settings()
