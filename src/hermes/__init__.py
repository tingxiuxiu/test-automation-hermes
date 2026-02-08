from typing import overload

from ._android.android_device import AndroidDevice
from ._core.step import step
from ._core import hermes_cache
from .models.device import (
    AndroidDeviceModel,
    HarmonyDeviceModel,
    IOSDeviceModel,
)

__version__ = "0.1.0"


@overload
def new_device(
    device_model: AndroidDeviceModel,
) -> AndroidDevice: ...


@overload
def new_device(device_model: IOSDeviceModel) -> AndroidDevice: ...


@overload
def new_device(device_model: HarmonyDeviceModel) -> AndroidDevice: ...


def new_device(
    device_model: AndroidDeviceModel | IOSDeviceModel | HarmonyDeviceModel,
):
    device = AndroidDevice(device_model)
    hermes_cache.add_device(device_model.tag, device)
    return device


__all__ = ["__version__", "step", "new_device"]
