from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://watchdog:watchdog_dev@localhost:5432/watchdog"
    database_url_sync: str = "postgresql://watchdog:watchdog_dev@localhost:5432/watchdog"
    redis_url: str = "redis://localhost:6379/0"
    anthropic_api_key: str = ""
    data_dir: Path = Path("./data")
    archive_dir: Path | None = None
    log_level: str = "INFO"

    # Pipeline settings
    chunk_size_tokens: int = 3000
    chunk_overlap_tokens: int = 200
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    claude_model: str = "claude-sonnet-4-5-20250929"
    max_concurrent_api_calls: int = 5
    download_limit: int = 100

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"


settings = Settings()
