__version__ = "0.1.0"

from typing import overload

from ._android.android_device import AndroidDevice
from ._core.hermes_cache import HermesCache
from ._core.step import step
from .models.device import (
    AndroidDeviceAppiumModel,
    AndroidDeviceU2Model,
    HarmonyDeviceHypiumModel,
    IOSDeviceAppiumModel,
)

hermes_cache = HermesCache()


@overload
def new_device(
    device_model: AndroidDeviceAppiumModel | AndroidDeviceU2Model,
) -> AndroidDevice: ...
@overload
def new_device(device_model: IOSDeviceAppiumModel) -> AndroidDevice: ...
@overload
def new_device(device_model: HarmonyDeviceHypiumModel) -> AndroidDevice: ...


def new_device(
    device_model: AndroidDeviceAppiumModel
    | AndroidDeviceU2Model
    | IOSDeviceAppiumModel
    | HarmonyDeviceHypiumModel,
):
    device = AndroidDevice(device_model)
    hermes_cache.add_device(device_model.tag, device)
    return device


__all__ = ["step", "new_device"]
