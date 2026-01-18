import typing

if typing.TYPE_CHECKING:
    from .._android.android_device import AndroidDevice


class HermesCache:
    def __init__(self):
        self._devices: dict[str, AndroidDevice] = {}
        self._steps: list[str] = []

    def get_device(self, tag: str) -> AndroidDevice | None:
        return self._devices.get(tag)

    def add_device(self, tag: str, device: AndroidDevice) -> None:
        self._devices[tag] = device

    def remove_device(self, tag: str) -> None:
        if tag in self._devices:
            del self._devices[tag]

    def get_devices(self) -> list[tuple[str, AndroidDevice]]:
        return list(self._devices.items())
