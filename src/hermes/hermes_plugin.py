from uuid import uuid4

from ._plugins.case_listener import CaseListener
from ._plugins.device_linstener import DeviceListener
from ._plugins.hermes_listener import HermesListener
from .models.plugin import PluginOptions


def pytest_addoption(parser):
    parser.addoption("--hermes", action="store_true", help="enable hermes plugin")
    parser.addoption(
        "--hermes-uuid",
        type=str,
        default=str(uuid4()).replace("-", ""),
        dest="hermes_uuid",
        help="hermes uuid",
    )
    parser.addoption(
        "--hermes-randon-seed",
        type=int,
        dest="hermes_random_seed",
        help="hermes random seed",
    )
    parser.addoption(
        "--hermes-device-check",
        action="store_true",
        dest="hermes_device_check",
        help="hermes device check",
    )


def pytest_configure(config):
    if config.getoption("--hermes"):
        options = PluginOptions(
            hermes_uuid=config.getoption("--hermes-uuid"),
            hermes_random_seed=config.getoption("--hermes-randon-seed"),
            hermes_device_check=config.getoption("--hermes-device-check"),
        )
        listener = HermesListener(options)
        config.pluginmanager.register(listener, "hermes_listener")
        config.pluginmanager.register(CaseListener(), "hermes_case_listener")
        if config.getoption("--hermes-device-check"):
            config.pluginmanager.register(DeviceListener(), "hermes_device_listener")
