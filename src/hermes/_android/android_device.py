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
    """
    AndroidDevice class for managing Android device connections and interactions.

    This class provides functionality to connect to Android devices, set up the portal service,
    and manage device state. It serves as the main interface for interacting with Android devices
    through the Hermes test automation framework.

    Attributes:
        _device_model: AndroidDeviceModel - The device model containing device configuration
        _driver: DriverProtocol | None - The driver for interacting with the device
        _language: Language - The language setting for the device
        _adb: AndroidADB - ADB interface for device communication
        _timeout: int - Default timeout for operations
        _port: int - Port for portal service communication
    """

    def __init__(self, device_model: AndroidDeviceModel):
        """
        Initialize an AndroidDevice instance.

        Args:
            device_model: AndroidDeviceModel - The device model containing configuration details

        Raises:
            ValueError: If the device serial is an empty string
        """
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
        """
        Get the device model.

        Returns:
            AndroidDeviceModel - The device model containing device configuration
        """
        return self._device_model

    def set_language(self, language: Language):
        """
        Set the language for the device.

        Args:
            language: Language - The language to set
        """
        self._language = language

    def set_implicitly_wait(self, timeout: int):
        """
        Set the implicit wait timeout for operations.

        Args:
            timeout: int - The timeout in milliseconds
        """
        self._timeout = timeout

    def connect(self):
        """
        Connect to the Android device.

        This method sets up the portal service, verifies the connection, and initializes the driver.

        Raises:
            ConnectionError: If the portal server is not responsive
        """
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
        """
        Check if the portal app is installed on the device.

        Returns:
            bool - True if the portal app is installed, False otherwise
        """
        return self._adb.get_app_info("com.hermes.portal") is not None

    def _install_portal(self):
        """
        Install the portal app on the device if it's not already installed.

        This method downloads the portal APK from the configured URL and installs it.
        """
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
        """
        Set up the portal service on the device.

        This method installs the portal app if needed, starts it, enables accessibility service,
        forwards the port, and enables the service.

        Args:
            port: int - The port to use for portal service communication
        """
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
        """
        Ping the portal server to check if it's responsive.

        Returns:
            bool - True if the portal server is responsive, False otherwise
        """
        return portal_http.ping()

    def _set_token(self) -> str:
        """
        Extract and set the authentication token from the portal service.

        Returns:
            str - The extracted authentication token

        Raises:
            ValueError: If no valid token is found
        """
        res = self._adb.query_content(PortalContent.AUTH_TOKEN)
        pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        search_res = re.search(pattern, res)
        if not search_res:
            raise ValueError("token is empty")
        return search_res.group()

    def disconnect(self):
        """
        Disconnect from the Android device.

        This method releases the portal port, removes port forwarding, and cleans up the driver.
        """
        if self._port:
            hermes_cache.release_portal_port(self._port)
            self._adb.remove_forward_port(self._port)
        if self._driver:
            self._driver = None

    def reconnect(self):
        """
        Reconnect to the Android device.

        This method disconnects and then reconnects to the device.
        """
        self.disconnect()
        self.connect()

    @property
    def driver(self) -> DriverProtocol:
        """
        Get the driver for interacting with the device.

        Returns:
            DriverProtocol - The driver instance

        Raises:
            ValueError: If the driver is not initialized
        """
        if not self._driver:
            raise ValueError("driver is not initialized")
        return self._driver

    @property
    def adb(self) -> DebugBridgeProtocol:
        """
        Get the ADB interface for device communication.

        Returns:
            DebugBridgeProtocol - The ADB interface instance
        """
        return self._adb

    def media_calcualte(self):
        """
        Placeholder method for media calculation functionality.
        """
        ...
