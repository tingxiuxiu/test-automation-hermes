import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=os.environ.get("HERMERS_ENV"),
        extra="ignore",
    )
    PORTAL_DOWNLOAD_URL: str = "https://github.com/portal-0.1.0.apk"
    PORTAL_PACKAGE_NAME: str = "com.hermes.portal"
    PORTAL_ACCESSIBILITY_SERVICE: str = (
        "com.hermes.portal/com.hermes.portal.HermesAccessibilityService"
    )
    PORTAL_SOCKET_SERVER_PORT: int = 8080

    CACHE_DIR: Path = Path.cwd() / "cache"

    @field_validator("CACHE_DIR")
    def v_cache_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    LOG_DIR: Path = CACHE_DIR / "logs"

    @field_validator("LOG_DIR")
    def v_log_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    LOG_LEVEL: str = "INFO"

    LOG_FORMAT: str = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | hermes v0.1.0 | "
        "<level>{level: <8}</level> | "
        "{name}:{function}:{line} - <level>{message}</level>"
    )

    OCR_API_KEY: str = ""
    YOLO_API_KEY: str = ""
