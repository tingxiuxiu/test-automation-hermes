import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Literal, overload

from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .._core import config
from .._protocol.component_protocol import ComponentProtocol
from .._protocol.driver_protocol import DriverProtocol
from ..models.component import Box, Point, Size
from ..models.language import Language
from ..models.selector import Selector, SelectorKey
from .android_component import AndroidComponent
from .selector_paser import SelectorParser


class AndroidDriver(DriverProtocol):
    def __init__(
        self, driver: WebDriver, name: str, language: Language, timeout: int = 8000
    ):
        self._driver = driver
        self._name = name
        self._language = language
        self._timeout = timeout
        self._window_size: Size | None = None
        driver.implicitly_wait(timeout / 1000)

    def get_window_size(self, refresh: bool = False) -> Size:
        if refresh or not self._window_size:
            _size = self._driver.get_window_size()
            self._window_size = Size(width=_size["width"], height=_size["height"])
        return self._window_size

    @property
    def page_source(self) -> str:
        return self._driver.page_source

    def tap(self, target: ComponentProtocol | Selector | Point):
        if isinstance(target, AndroidComponent):
            target.tap()
        elif isinstance(target, Selector):
            self.locator(target).tap()
        elif isinstance(target, Point):
            self._driver.tap([(target.x, target.y)])
        else:
            raise ValueError("Invalid target type")

    def long_press(
        self, target: ComponentProtocol | Selector | Point, duration: int = 2000
    ):
        if isinstance(target, AndroidComponent):
            target.long_press(duration)
        elif isinstance(target, Selector):
            self.locator(target).long_press(duration)
        elif isinstance(target, Point):
            self._driver.tap([(target.x, target.y)], duration)
        else:
            raise ValueError("Invalid target type")

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> AndroidComponent:
        if language is None:
            language = self._language
        parser = SelectorParser(selector, language, combination)
        return AndroidComponent(
            driver=self._driver,
            name=self._name,
            element=self._driver.find_element(parser.get_by(), parser.get_value()),
            language=language,
            timeout=self._timeout,
            monitor=parser.get_monitor(),
        )

    def locators(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[AndroidComponent]:
        if language is None:
            language = self._language
        parser = SelectorParser(selector, language, combination)
        return [
            AndroidComponent(
                driver=self._driver,
                name=self._name,
                element=ele,
                language=language,
                timeout=self._timeout,
                monitor=parser.get_monitor(),
            )
            for ele in self._driver.find_elements(parser.get_by(), parser.get_value())
        ]

    @overload
    def wait_for(
        self,
        selector: Selector,
        *,
        visible: Literal[True],
        timeout: int = 15000,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> AndroidComponent: ...

    @overload
    def wait_for(
        self,
        selector: Selector,
        *,
        visible: Literal[False],
        timeout: int = 15000,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> bool: ...

    def wait_for(
        self,
        selector: Selector,
        *,
        visible: bool = True,
        timeout: int = 15000,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> AndroidComponent | bool:
        if language is None:
            language = self._language
        parser = SelectorParser(selector, language, combination)
        wait = WebDriverWait(self._driver, timeout / 1000)
        if visible:
            ele = wait.until(
                EC.presence_of_element_located((parser.get_by(), parser.get_value()))
            )
            return AndroidComponent(
                driver=self._driver,
                name=self._name,
                element=ele,  # type: ignore
                language=language,
                timeout=timeout,
                monitor=parser.get_monitor(),
            )
        else:
            ele = wait.until_not(
                EC.presence_of_element_located((parser.get_by(), parser.get_value()))
            )
            return ele is None

    def scroll_into_view(
        self,
        target: Selector,
        scrollable: Selector | Box,
        *,
        horizontal: bool = False,
        target_combination: Sequence[SelectorKey] | None = None,
        scrollable_combination: Sequence[SelectorKey] | None = None,
        target_language: Language | None = None,
        scrollable_language: Language | None = None,
    ) -> AndroidComponent:
        if target_language is None:
            target_language = self._language
        if scrollable_language is None:
            scrollable_language = self._language
        target_s = SelectorParser(target, target_language, target_combination)
        if isinstance(scrollable, Box):
            start = Point(
                x=int(scrollable.left + scrollable.width / 2),
                y=int(scrollable.top + scrollable.height / 2),
            )
            end = Point(
                x=int(scrollable.left + scrollable.width / 2),
                y=int(scrollable.bottom * 0.7 + scrollable.height / 2),
            )
            for _ in range(8):
                self.swipe(start, end, wait_render=500)
                if ele := self.wait_for(
                    target,
                    visible=True,
                    combination=target_combination,
                    language=target_language,
                    timeout=1000,
                ):
                    return ele
            raise Exception("Scroll into view failed")
        else:
            scrollable_s = SelectorParser(
                scrollable, scrollable_language, scrollable_combination
            )
            if horizontal:
                uiautomator_t = f"new UiScrollable({scrollable_s.get_value()}.scrollable(true)).setAsHorizontalList().scrollIntoView({target_s.get_value()})"
            else:
                uiautomator_t = f"new UiScrollable({scrollable_s.get_value()}.scrollable(true)).setAsVerticalList().scrollIntoView({target_s.get_value()})"
            ele = self._driver.find_element(target_s.get_by(), uiautomator_t)
            return AndroidComponent(
                driver=self._driver,
                name=self._name,
                element=ele,
                language=target_language,
                timeout=self._timeout,
                monitor=target_s.get_monitor(),
            )

    def drag_and_drop(
        self,
        start: ComponentProtocol | Selector | Point,
        end: ComponentProtocol | Selector | Point,
        *,
        duration: int = 2000,
    ) -> None:
        if isinstance(start, Point):
            _start = start
        elif isinstance(start, Selector):
            _start = self.wait_for(start, visible=True).center()
        else:
            _start = start.center()

        if isinstance(end, Point):
            _end = end
        elif isinstance(end, Selector):
            _end = self.wait_for(end, visible=True).center()
        else:
            _end = end.center()
        touch_input = PointerInput(interaction.POINTER_TOUCH, "touch")
        action = ActionChains(self._driver)
        action.w3c_actions = ActionBuilder(self._driver, mouse=touch_input)
        action.w3c_actions.pointer_action.move_to_location(
            _start.x, _start.y
        ).pointer_down().pause(duration / 1000).move_to_location(
            _end.x, _end.y
        ).pointer_up().release()
        action.perform()

    def swipe(
        self,
        start: ComponentProtocol | Selector | Point,
        end: ComponentProtocol | Selector | Point,
        *,
        duration: int = 2000,
        repeat: int = 1,
        wait_render: int = 500,
    ) -> None:
        if isinstance(start, Point):
            _start = start
        elif isinstance(start, Selector):
            _start = self.wait_for(start, visible=True).center()
        else:
            _start = start.center()

        if isinstance(end, Point):
            _end = end
        elif isinstance(end, Selector):
            _end = self.wait_for(end, visible=True).center()
        else:
            _end = end.center()
        for _ in range(repeat):
            self._driver.swipe(
                start_x=_start.x,
                start_y=_start.y,
                end_x=_end.x,
                end_y=_end.y,
                duration=duration,
            )
            time.sleep(wait_render / 1000)

    def zoom_in(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        scale: float = 0.5,
        duration: int = 200,
        wait_render: int = 500,
    ):
        if isinstance(target, Point):
            _target = target
        elif isinstance(target, Selector):
            _target = self.wait_for(target, visible=True).center()
        else:
            _target = target.center()
        w_size = self.get_window_size()
        m_size = Point(
            x=int(w_size.width / 2 * scale), y=int(w_size.height / 2 * scale)
        )
        f1 = PointerInput(interaction.POINTER_TOUCH, "touch")
        f2 = PointerInput(interaction.POINTER_TOUCH, "touch2")
        action = ActionBuilder(self._driver)
        action._add_input(f1)
        action._add_input(f2)

        action.pointer_action.move_to_location(_target.x + m_size.x, _target.y)
        action.pointer_action.pointer_down()
        action.pointer_action.pause(duration / 1000)
        action.pointer_action.move_to_location(_target.x, _target.y)
        action.pointer_action.pointer_up()

        action.pointer_action.move_to_location(_target.x, _target.y + m_size.y)
        action.pointer_action.pointer_down()
        action.pointer_action.pause(duration / 1000)
        action.pointer_action.move_to_location(_target.x, _target.y)
        action.pointer_action.pointer_up()

        action.perform()
        time.sleep(wait_render / 1000)

    def zoom_out(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        scale: float = 0.5,
        duration: int = 200,
        wait_render: int = 500,
    ):
        if isinstance(target, Point):
            _target = target
        elif isinstance(target, Selector):
            _target = self.wait_for(target, visible=True).center()
        else:
            _target = target.center()
        w_size = self.get_window_size()
        m_size = Point(
            x=int(w_size.width / 2 * scale), y=int(w_size.height / 2 * scale)
        )
        f1 = PointerInput(interaction.POINTER_TOUCH, "touch")
        f2 = PointerInput(interaction.POINTER_TOUCH, "touch2")
        action = ActionBuilder(self._driver)
        action._add_input(f1)
        action._add_input(f2)

        action.pointer_action.move_to_location(_target.x, _target.y)
        action.pointer_action.pointer_down()
        action.pointer_action.pause(duration / 1000)
        action.pointer_action.move_to_location(_target.x + m_size.x, _target.y)
        action.pointer_action.pointer_up()

        action.pointer_action.move_to_location(_target.x, _target.y)
        action.pointer_action.pointer_down()
        action.pointer_action.pause(duration / 1000)
        action.pointer_action.move_to_location(_target.x, _target.y + m_size.y)
        action.pointer_action.pointer_up()

        action.perform()
        time.sleep(wait_render / 1000)

    def screenshot(self, path: Path | None = None) -> Path:
        if path is None:
            path = (
                config.CACHE_DIR
                / f"{self._name}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-screenshot.png"
            )
        self._driver.save_screenshot(path)
        return path
