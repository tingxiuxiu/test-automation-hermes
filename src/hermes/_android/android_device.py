import re
import time

import httpx

from ..protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..protocol.device_protocol import DeviceProtocol
from ..protocol.driver_protocol import DriverProtocol
from ..models.device import AndroidDeviceModel
from ..models.language import Language
from .android_driver import AndroidDriver
from .android_adb import AndroidADB
from .._core import config, hermes_cache, portal_http
from .._core.portal_protocol import PortalContent


class AndroidDevice(DeviceProtocol):
    def __init__(self, device_model: AndroidDeviceModel):
        if device_model.serial == "":
            raise ValueError("serial can not be empty string")
        self._device_model = device_model
        self._driver: DriverProtocol | None = None
        self._language = device_model.language
        self._adb = AndroidADB(
            serial=device_model.serial,
            android_home=device_model.android_home,
            capture_logcat=device_model.capture_logcat,
        )
        self._timeout = device_model.timeout
        self._port: int = hermes_cache.get_portal_port()

    @property
    def device_model(self) -> AndroidDeviceModel:
        return self._device_model

    def set_language(self, language: Language):
        self._language = language

    def set_implicitly_wait(self, timeout: int):
        self._timeout = timeout

    def connect(self):
        if self._driver:
            return
        self._setup_portal(self._port)
        if not self.ping():
            raise ConnectionError("Portal server not responsive")
        self._driver = AndroidDriver(
            tag=self._device_model.tag,
            adb=self._adb,
            token="",
            language=self._language,
            locator_engine=self._device_model.locator_engine,
            timeout=self._device_model.timeout,
        )
        return

    def _check_portal_installed(self) -> bool:
        return self._adb.get_app_info("com.hermes.portal") is not None

    def _install_portal(self):
        if self._check_portal_installed():
            return
        with httpx.Client() as client:
            tmp_file = config.CACHE_DIR / "app-debug.apk"
            response = client.get(config.PORTAL_DOWNLOAD_URL)
            response.raise_for_status()
            with open(tmp_file, "wb") as f:
                f.write(response.content)
            self._adb.install(tmp_file)

    def _setup_portal(self, port: int):
        self._install_portal()
        self._adb.start_app("com.hermes.portal", ".MainActivity")
        for _ in range(10):
            if self._adb.get_pid("com.hermes.portal") != -1:
                break
            time.sleep(1)
        if not self._adb.check_accessibility_service(
            config.PORTAL_ACCESSIBILITY_SERVICE
        ):
            self._adb.set_accessibility_service(config.PORTAL_ACCESSIBILITY_SERVICE)
            assert self._adb.check_accessibility_service(
                config.PORTAL_ACCESSIBILITY_SERVICE
            )
            # assert self._adb.insert_content(PortalContent.ENABLE_SOCKET_SERVER)
        self._adb.forward_port(port, config.PORTAL_SERVICE_PORT)
        self._adb.query_content(PortalContent.ENABLE_SERVICE)
        portal_http.set_port(port)

    def ping(self) -> bool:
        return portal_http.ping()

    def _set_token(self) -> str:
        res = self._adb.query_content(PortalContent.AUTH_TOKEN)
        pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        search_res = re.search(pattern, res)
        if not search_res:
            raise ValueError("token is empty")
        return search_res.group()

    def disconnect(self):
        if self._port:
            hermes_cache.release_portal_port(self._port)
            self._adb.remove_forward_port(self._port)
        if self._driver:
            self._driver.close()
            self._driver = None

    def reconnect(self):
        self.disconnect()
        self.connect()

    @property
    def driver(self) -> DriverProtocol:
        if not self._driver:
            raise ValueError("driver is not initialized")
        return self._driver

    @property
    def adb(self) -> DebugBridgeProtocol:
        return self._adb

    def media_calcualte(self): ...
