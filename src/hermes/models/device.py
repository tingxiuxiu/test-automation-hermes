from enum import Enum
from uuid import uuid4

from pydantic import BaseModel

from .language import Language


class PlatformName(Enum):
    ANDROID = "android"
    IOS = "ios"
    HARMONY = "harmony"


class LocatorEngine(Enum):
    XPATH = "xpath"
    JSONPATH = "jsonpath"


class BaseDeviceModel(BaseModel):
    serial: str
    language: Language = Language.CHINESE
    timeout: int = 5000
    tag: str = uuid4().hex


class AndroidDeviceModel(BaseDeviceModel):
    platform_name: PlatformName = PlatformName.ANDROID
    locator_engine: LocatorEngine = LocatorEngine.XPATH
    app_package: str | None = None
    app_activity: str | None = None
    android_home: str | None = None
    capture_logcat: bool = False


class IOSDeviceModel(BaseDeviceModel): ...


class HarmonyDeviceModel(BaseDeviceModel): ...
