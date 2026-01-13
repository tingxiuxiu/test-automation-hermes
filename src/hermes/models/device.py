from enum import Enum

from pydantic import BaseModel

from .language import Language


class DriverType(Enum):
    APPIUM = 0
    U2 = 1
    HYPIUM = 2


class PlatformName(Enum):
    ANDROID = "android"
    IOS = "ios"
    HARMONY = "harmony"


class AutomationName(Enum):
    UIAUTOMATOR2 = "UiAutomator2"
    XCUITEST = "XCUITest"
    APPIUM = "Appium"
    HYPIMUM = "Hypium"


class BaseDeviceModel(BaseModel):
    serial: str
    name: str
    language: Language = Language.CHINESE
    timeout: int = 8000
    tag: str | None = None


class AndroidDeviceAppiumModel(BaseDeviceModel):
    appium_host: str = "http://127.0.0.1/4723"
    platform_name: PlatformName = PlatformName.ANDROID
    automation_name: AutomationName = AutomationName.UIAUTOMATOR2
    app_package: str | None = None
    app_activity: str | None = None
    android_home: str | None = None
    no_reset: bool = True


class AndroidDeviceU2Model(BaseDeviceModel): ...


class IOSDeviceAppiumModel(BaseDeviceModel): ...


class HarmonyDeviceHypiumModel(BaseDeviceModel): ...
