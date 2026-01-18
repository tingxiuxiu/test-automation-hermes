from appium.webdriver.webdriver import WebDriver

from .._protocol.debug_bridge_protocol import DebugBridgeProtocol
from .._protocol.device_protocol import DeviceProtocol
from .._protocol.driver_protocol import DriverProtocol
from ..models.device import AndroidDeviceAppiumModel, AndroidDeviceU2Model, DriverType
from ..models.language import Language
from .android_driver import AndroidDriver


class AndroidDevice(DeviceProtocol):
    def __init__(self, device_model: AndroidDeviceAppiumModel | AndroidDeviceU2Model):
        if device_model.serial == "":
            raise ValueError("serial can not be empty string")
        self._device_model = device_model
        if isinstance(device_model, AndroidDeviceAppiumModel):
            self._initial_driver: WebDriver | None = None
            self._driver_type = DriverType.APPIUM
        else:
            self._initial_driver = None
            self._driver_type = DriverType.U2
        self._driver: DriverProtocol | None = None
        self._language = device_model.language

    @property
    def device_model(self):
        return self._device_model

    def _set_appium(self):
        if not isinstance(self._device_model, AndroidDeviceAppiumModel):
            raise ValueError("device model is not AndroidDeviceAppiumModel")
        from appium.options.android.uiautomator2.base import UiAutomator2Options
        from appium.webdriver.client_config import AppiumClientConfig

        desire_caps = {
            "platformName": self._device_model.platform_name.value,
            "automationName": self._device_model.automation_name.value,
            "appPackage": self._device_model.app_package,
            "appActivity": self._device_model.app_activity,
            "androidHome": self._device_model.android_home,
            "newCommandTimeout": 60,
            "adbExecTimeout": 60,
            "waitForIdleTimeout": 200,
            "noReset": self._device_model.no_reset,
        }
        client_config = AppiumClientConfig(
            remote_server_addr=self._device_model.appium_host,
            direct_connection=True,
            keep_alive=True,
            ignore_certificates=True,
        )
        options = UiAutomator2Options().load_capabilities(desire_caps)
        return options, client_config

    @property
    def inital_driver(self) -> WebDriver:
        if not self._initial_driver:
            raise ValueError("driver is not initialized")
        return self._initial_driver

    def set_language(self, language: Language):
        self._language = language

    def connect(self):
        if self._driver:
            return
        if isinstance(self._device_model, AndroidDeviceAppiumModel):
            options, client_config = self._set_appium()
            self._initial_driver = WebDriver(
                command_executor=client_config.remote_server_addr,
                options=options,
                client_config=client_config,
            )
            self._driver = AndroidDriver(
                driver=self._initial_driver,
                name=self._device_model.name,
                language=self._language,
                timeout=self._device_model.timeout,
            )
            return
        else:
            raise ValueError("driver type is not supported")

    def disconnect(self):
        if self._initial_driver:
            if self._driver_type == DriverType.APPIUM:
                self._initial_driver.quit()
            else:
                self._initial_driver.close()
            self._driver = None

    def reconnect(self):
        self.disconnect()
        self.connect()

    def check_driver(self) -> bool:
        if self._initial_driver:
            if self._driver_type == DriverType.APPIUM:
                return self._initial_driver.get_window_size() is not None
            else:
                return self._initial_driver.session_id is not None
        return False

    @property
    def driver(self) -> DriverProtocol:
        if not self._driver:
            raise ValueError("driver is not initialized")
        return self._driver

    def adb(self) -> DebugBridgeProtocol: ...

    def ai(self): ...
