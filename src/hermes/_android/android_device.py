import re
import time

import httpx

from loguru import logger

from ..protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..protocol.device_protocol import DeviceProtocol
from ..protocol.driver_protocol import DriverProtocol
from ..models.device import AndroidDeviceModel
from ..models.language import Language
from .android_driver import AndroidDriver
from .android_adb import AndroidADB
from .._core import config, hermes_cache
from .._core.portal_protocol import PortalContent, PortalHTTP


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
        self._base_url: str = f"http://127.0.0.1:{self._port}"
        self._client: httpx.Client = httpx.Client(timeout=3)

    def __del__(self):
        self._client.close()

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
        self._adb.click_home()
        self._driver = AndroidDriver(
            adb=self._adb,
            base_url=self._base_url,
            # token=self._set_token(),
            token="",
            client=self._client,
            tag=self._device_model.tag,
            language=self._language,
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
        self._adb.forward_port(port, config.PORTAL_SOCKET_SERVER_PORT)
        self._adb.query_content(PortalContent.ENABLE_SERVICE)

    def ping(self) -> bool:
        url = f"{self._base_url}{PortalHTTP.PING}"
        logger.info(f"Ping portal server: {url}")
        for i in range(10):
            try:
                response = self._client.get(url)
            except Exception as e:
                logger.warning(f"Ping portal server failed: {e}, retry {i}")
                time.sleep(1)
                continue
            if response.status_code == 200:
                return True
            time.sleep(1)
        return False

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
