from hermes import new_device
from hermes.models.device import AndroidDeviceModel
from loguru import logger

from hermes.models.selector import Selector, SelectorKey
from hermes.models.component import Point, Size, Bounds


class TestDriver:
    d = new_device(AndroidDeviceModel(serial="emulator-5554"))

    def setup_class(self):
        self.d.connect()
        self.d.adb.start_app("com.android.settings/.Settings")

    def teardown_class(self):
        self.d.adb.stop_app("com.android.settings")
        self.d.disconnect()

    def test_component(self):
        self.d.driver.swipe(Point(x=500, y=2465), Point(x=500, y=2000))
        selector = Selector(text="Battery")
        component = self.d.driver.locator(selector)
        assert component is not None
        logger.info(component)
        assert component.get_window() is not None
        assert component.get_text() == "Battery"
        assert component.get_description() == ""
        assert component.get_size() == Size(width=420 - 261, height=1498 - 1431)

        assert component.is_visible() is True
        assert component.is_selected() is False
        assert component.is_enabled() is True
        assert component.get_attribute("class") == "android.widget.TextView"

    def test_tap(self):
        selector = Selector(text="Search Settings")
        component = self.d.driver.locator(selector)
        assert component is not None
        assert component.get_center() == Point(x=451, y=297)
        assert component.get_bounds() == Bounds(
            left=223, top=256, right=680, bottom=339
        )
        component.tap()
        selector = Selector(
            text="Search settings", class_name="android.widget.EditText"
        )
        component = self.d.driver.locator(
            selector, combination=[SelectorKey.CLASS_NAME, SelectorKey.TEXT]
        )
        assert component is not None

    def test_input(self):
        selector = Selector(
            text="Search settings", class_name="android.widget.EditText"
        )
        component = self.d.driver.locator(
            selector, combination=[SelectorKey.CLASS_NAME, SelectorKey.TEXT]
        )
        assert component is not None
        self.d.driver.input_text(0, "123456你好helloworld")
        selector = Selector(
            text="Search settings", class_name="android.widget.EditText"
        )
        component = self.d.driver.locator(
            selector, combination=[SelectorKey.CLASS_NAME]
        )
        assert component is not None
        assert component.get_text() == "123456你好helloworld"

    def test_clear(self):
        selector = Selector(
            text="Search settings", class_name="android.widget.EditText"
        )
        component = self.d.driver.locator(
            selector, combination=[SelectorKey.CLASS_NAME]
        )
        assert component is not None
        self.d.driver.clear_text(0)
        selector = Selector(
            text="Search settings", class_name="android.widget.EditText"
        )
        component = self.d.driver.locator(
            selector, combination=[SelectorKey.CLASS_NAME]
        )
        assert component is not None
        assert component.get_text() == "Search settings"
