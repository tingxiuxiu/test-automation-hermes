from typing import Protocol

from ..models.language import Language
from .debug_bridge_protocol import DebugBridgeProtocol
from .driver_protocol import DriverProtocol


class DeviceProtocol(Protocol):
    def connect(self): ...

    def disconnect(self): ...

    def reconnect(self): ...

    def set_language(self, language: Language): ...

    @property
    def driver(self) -> DriverProtocol: ...

    def set_driver(self, driver: DriverProtocol): ...

    def implicitly_wait(self, timeout: int):
        """
        设置隐式等待时间

        :param timeout: 隐式等待时间 ms
        """
        ...

    def check_driver(self) -> bool: ...

    def debug_bridge(self) -> DebugBridgeProtocol: ...

    def media_calcualte(self): ...
