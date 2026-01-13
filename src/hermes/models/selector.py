from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class Monitor(BaseModel):
    name: str
    id: str
    uid: str


class MultiLanguageSelector(BaseModel):
    chinese: str | None = None
    english: str | None = None
    japanese: str | None = None
    korean: str | None = None
    german: str | None = None
    french: str | None = None


class MultiLanguageImageSelector(BaseModel):
    chinese: Path | None = None
    english: Path | None = None
    japanese: Path | None = None
    korean: Path | None = None
    german: Path | None = None
    french: Path | None = None


class ImageSelector(BaseModel):
    path: MultiLanguageImageSelector
    threshold: float = 0.9


class Selector(BaseModel):
    id: MultiLanguageSelector | str | None = None
    text: MultiLanguageSelector | str | None = None
    description: MultiLanguageSelector | str | None = None
    xpath: MultiLanguageSelector | str | None = None
    text_starts_with: MultiLanguageSelector | str | None = None
    text_ends_with: MultiLanguageSelector | str | None = None
    text_contains: MultiLanguageSelector | str | None = None
    text_matches: MultiLanguageSelector | str | None = None
    description_starts_with: MultiLanguageSelector | str | None = None
    description_ends_with: MultiLanguageSelector | str | None = None
    description_contains: MultiLanguageSelector | str | None = None
    description_matches: MultiLanguageSelector | str | None = None
    android_uiautomator: MultiLanguageSelector | str | None = None
    class_name: MultiLanguageSelector | str | None = None
    image: ImageSelector | None = None
    monitor: Monitor | None = None

    def to_dict(self) -> dict:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()


class SelectorKey(Enum):
    ID = "id"
    TEXT = "text"
    DESCRIPTION = "description"
    XPATH = "xpath"
    CLASS_NAME = "class_name"
    TEXT_STARTS_WITH = "text_starts_with"
    TEXT_ENDS_WITH = "text_ends_with"
    TEXT_CONTAINS = "text_contains"
    TEXT_MATCHES = "text_matches"
    DESCRIPTION_STARTS_WITH = "description_starts_with"
    DESCRIPTION_ENDS_WITH = "description_ends_with"
    DESCRIPTION_CONTAINS = "description_contains"
    DESCRIPTION_MATCHES = "description_matches"
    ANDROID_UIAUTOMATOR = "android_uiautomator"
    IMAGE = "image"
