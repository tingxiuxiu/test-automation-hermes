from loguru import logger

from hermes import new_device
from hermes.models.device import AndroidDeviceModel

from hermes.models.selector import Selector, SelectorKey


class TestDriver:
    d = new_device(AndroidDeviceModel(serial="emulator-5554"))

    def setup_class(self):
        self.d.connect()
        self.d.adb.start_app("com.android.settings/.Settings")

    def teardown_class(self):
        self.d.adb.stop_app("com.android.settings")
        self.d.disconnect()

    def test_get_window_size(self):
        """测试获取窗口大小"""
        size = self.d.driver.get_window_size()
        assert size.width == 1080
        assert size.height == 2400

    def test_get_xml_tree(self):
        """测试获取页面"""
        page = self.d.driver.get_xml_tree(0)
        logger.info(page)
        assert "Battery" in page

    def test_get_json_tree(self):
        """测试获取界面树"""
        tree = self.d.driver.get_json_tree(0)
        logger.info(tree)
        assert tree is not None

    def test_tap_with_selector(self):
        """测试点击元素"""
        # 189, 1683, 357, 1754
        selector = Selector(text="Battery")
        self.d.driver.tap(selector)
        selector = Selector(text="Battery usage")
        element = self.d.driver.locator(selector)
        assert element is not None
        assert element.get_text() == "Battery usage"

    def test_tap_with_point(self):
        """测试点击坐标"""
        selector = Selector(description="Navigate up")
        element = self.d.driver.locator(selector)
        assert element is not None
        self.d.driver.tap(element.get_center())
        selector = Selector(text="Apps")
        element = self.d.driver.locator(selector)
        assert element is not None
        assert element.get_text() == "Apps"

    def test_tap_with_component(self):
        """测试点击组件"""
        selector = Selector(text="Battery")
        component = self.d.driver.locator(selector)
        assert component is not None
        assert component.get_text() == "Battery"
        self.d.driver.tap(component)
        selector = Selector(text="Battery usage")
        element = self.d.driver.locator(selector)
        assert element is not None
        assert element.get_text() == "Battery usage"

    def test_locator_with_text(self):
        """测试定位元素"""
        selector = Selector(text="Battery")
        component = self.d.driver.locator(selector)
        assert component is not None
        assert component.get_text() == "Battery"

    def test_locator_with_description(self):
        """测试定位元素"""
        selector = Selector(description="Navigate up")
        element = self.d.driver.locator(selector)
        assert element is not None
        assert element.get_description() == "Navigate up"

    def test_locator_with_class_name(self):
        """测试定位元素"""
        selector = Selector(class_name="android.widget.TextView")
        component = self.d.driver.locator(selector)
        assert component is not None
        assert component.get_attribute("class") == "android.widget.TextView"

    # def test_locator_with_resource_id(self):
    #     """测试定位元素"""
    #     selector = Selector(id="com.android.settings:id/title")
    #     component = self.d.driver.locator(selector)
    #     assert component is not None

    def test_locator_with_xpath(self):
        """测试定位元素"""
        selector = Selector(xpath="//android.widget.TextView[@text='Battery']")
        component = self.d.driver.locator(selector)
        assert component is not None
        assert component.get_attribute("class") == "android.widget.TextView"
        assert component.get_text() == "Battery"

    def test_locator_with_combination(self):
        """测试定位元素"""
        selector = Selector(text="Battery", class_name="android.widget.TextView")
        component = self.d.driver.locator(
            selector, combination=[SelectorKey.TEXT, SelectorKey.CLASS_NAME]
        )
        assert component is not None
        assert component.get_attribute("class") == "android.widget.TextView"
        assert component.get_text() == "Battery"

    def test_locator_with_combination_2(self):
        """测试定位元素"""
        selector = Selector(
            description="Navigate up", class_name="android.widget.ImageButton"
        )
        component = self.d.driver.locator(
            selector, combination=[SelectorKey.DESCRIPTION, SelectorKey.CLASS_NAME]
        )
        assert component is not None
        assert component.get_attribute("class") == "android.widget.ImageButton"
        assert component.get_description() == "Navigate up"
