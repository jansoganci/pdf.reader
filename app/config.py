from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    extraction_provider: str = "fake"
    live_extraction: str = "0"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    anthropic_effort: str = "medium"
    anthropic_timeout_seconds: int = 180
    data_dir: Path = ROOT / "data"
    max_upload_bytes: int = 30 * 1024 * 1024
    max_pages: int = 40
    preprocessing_version: str = "1"
    grouping_rules_version: str = "1"
    normalization_version: str = "4"
    system_prompt_version: str = "1"

    @property
    def live_calls_allowed(self) -> bool:
        return self.live_extraction == "1"


settings = Settings()
