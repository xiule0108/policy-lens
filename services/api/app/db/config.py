from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://policylens:policylens@localhost:5432/policylens",
        alias="DATABASE_URL",
    )
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    storage_dir: str = Field(default="./storage", alias="STORAGE_DIR")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    allowed_upload_extensions: str = Field(
        default=".pdf,.docx,.txt,.md,.markdown,.html,.htm",
        alias="ALLOWED_UPLOAD_EXTENSIONS",
    )
    default_model_profile: str = Field(default="china_balanced", alias="DEFAULT_MODEL_PROFILE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_upload_extension_set(self) -> set[str]:
        extensions = set()
        for raw_extension in self.allowed_upload_extensions.split(","):
            extension = raw_extension.strip().lower()
            if not extension:
                continue
            if not extension.startswith("."):
                extension = f".{extension}"
            extensions.add(extension)
        return extensions


settings = Settings()
