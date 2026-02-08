from hermes import new_device
from hermes.models.device import AndroidDeviceModel
from loguru import logger

from hermes.models.language import Language
from hermes.models.selector import Selector


class TestDevice:
    d = new_device(AndroidDeviceModel(serial="emulator-5554"))

    def setup_class(self):
        self.d.connect()

    def teardown_class(self):
        self.d.disconnect()

    def test_set_implicitly_wait(self):
        self.d.set_implicitly_wait(9000)
        assert self.d._timeout == 9000

    def test_set_language(self):
        self.d.set_language(Language.ENGLISH)
        assert self.d._language == Language.ENGLISH

    def test_adb(self):
        res = self.d.adb.get_app_info("com.hermes.portal")
        logger.info(res)
        assert res is not None

    def test_driver(self):
        s = Selector(text="Gmail")
        res = self.d.driver.locator(s)
        logger.info(res)
        assert res is not None
