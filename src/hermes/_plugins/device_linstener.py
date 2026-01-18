from loguru import logger

from .. import hermes_cache


class DeviceListener:
    def pytest_runtest_logstart(
        self, nodeid: str, location: tuple[str, int | None, str | None]
    ):
        for tag, device in hermes_cache.get_devices():
            try:
                if not device.check_driver():
                    device.connect()
                else:
                    device.reconnect()
            except Exception as e:
                logger.error(f"Device {tag} connect failed: {e}")
