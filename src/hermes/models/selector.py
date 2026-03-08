from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from .language import Language
from .media import MatchMethod


class SelectorKey(Enum):
    ID = "id"
    TEXT = "text"
    DESCRIPTION = "description"
    XPATH = "xpath"
    JSONPATH = "jsonpath"
    CLASS_NAME = "class_name"
    TEXT_STARTS_WITH = "text_starts_with"
    TEXT_ENDS_WITH = "text_ends_with"
    TEXT_CONTAINS = "text_contains"
    TEXT_MATCHES = "text_matches"
    DESCRIPTION_STARTS_WITH = "description_starts_with"
    DESCRIPTION_ENDS_WITH = "description_ends_with"
    DESCRIPTION_CONTAINS = "description_contains"
    DESCRIPTION_MATCHES = "description_matches"
    IMAGE = "image"


class Method(Enum):
    XPATH = "xpath"
    JSONPATH = "jsonpath"
    IMAGE = "image"


class Window(BaseModel):
    name: str = "default"
    display_id: int = 0


class MultiLanguageSelector(BaseModel):
    chinese: str | None = None
    chinese_traditional: str | None = None
    english: str | None = None
    japanese: str | None = None
    korean: str | None = None
    german: str | None = None
    french: str | None = None

    def get_value(self, language: Language) -> str | None:
        return self.__getattribute__(language.value)


class ImageSelector(BaseModel):
    path: Path
    threshold: float = 0.9
    method: MatchMethod | None = None


class MultiLanguageImageSelector(BaseModel):
    chinese: ImageSelector | None = None
    chinese_traditional: ImageSelector | None = None
    english: ImageSelector | None = None
    japanese: ImageSelector | None = None
    korean: ImageSelector | None = None
    german: ImageSelector | None = None
    french: ImageSelector | None = None

    def get_value(self, language: Language) -> ImageSelector | None:
        return self.__getattribute__(language.value)


class Selector(BaseModel):
    id: MultiLanguageSelector | str | None = None
    text: MultiLanguageSelector | str | None = None
    description: MultiLanguageSelector | str | None = None
    xpath: MultiLanguageSelector | str | None = None
    jsonpath: MultiLanguageSelector | str | None = None
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
    image: ImageSelector | MultiLanguageImageSelector | None = None
    window: Window = Window()

    def to_dict(self) -> dict:
        return self.model_dump()

    def get_value(
        self, key: SelectorKey, language: Language
    ) -> ImageSelector | str | None:
        value = self.__getattribute__(key.value)
        if isinstance(value, MultiLanguageSelector):
            return value.get_value(language)
        elif isinstance(value, ImageSelector):
            return value
        elif isinstance(value, MultiLanguageImageSelector):
            return value.get_value(language)
        return value
