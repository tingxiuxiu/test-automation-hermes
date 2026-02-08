import typing
import queue

if typing.TYPE_CHECKING:
    from xml.etree.ElementTree import Element
    from .._android.android_device import AndroidDevice


class HermesCache:
    def __init__(self):
        self._devices: dict[str, AndroidDevice] = {}
        self._steps: list[str] = []
        self._token: str | None = None
        self._port_pool = queue.Queue()
        for i in range(8200, 8220):
            self._port_pool.put(i)
        self._nodes: typing.Optional["Element"] = None

    def get_nodes(self) -> typing.Optional["Element"]:
        return self._nodes

    def set_nodes(self, nodes: "Element"):
        self._nodes = nodes

    def get_device(self, tag: str) -> typing.Optional["AndroidDevice"]:
        return self._devices.get(tag)

    def add_device(self, tag: str, device: "AndroidDevice") -> None:
        self._devices[tag] = device

    def remove_device(self, tag: str) -> None:
        if tag in self._devices:
            del self._devices[tag]

    def get_devices(self) -> list[tuple[str, "AndroidDevice"]]:
        return list(self._devices.items())

    def get_portal_port(self) -> int:
        return self._port_pool.get_nowait()

    def release_portal_port(self, port: int) -> None:
        self._port_pool.put(port)

    def set_token(self, token: str) -> None:
        self._token = token

    def get_token(self) -> str | None:
        return self._token
