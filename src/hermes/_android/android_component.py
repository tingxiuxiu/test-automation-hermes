from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Literal, overload

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement
from hermes.models.language import Language
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .._core import config
from .._protocol.component_protocol import ComponentProtocol
from ..models.component import Box, Point, Size
from ..models.selector import Monitor, Selector, SelectorKey
from .selector_paser import SelectorParser


class AndroidComponent(ComponentProtocol):
    def __init__(
        self,
        driver: WebDriver,
        name: str,
        element: WebElement,
        language: Language,
        timeout: int,
        monitor: Monitor | None,
    ):
        self._driver = driver
        self._name = name
        self._element = element
        self._language = language
        self._monitor = monitor
        self._timeout = timeout
        _size = self._element.size
        _rect = self._element.rect
        self._size = Size(width=_size["width"], height=_size["height"])
        self._center = Point(
            x=_rect["x"] + _size["width"] / 2, y=_rect["y"] + _size["height"] / 2
        )
        self._box = Box(
            left=_rect["x"],
            top=_rect["y"],
            right=_rect["x"] + _size["width"],
            bottom=_rect["y"] + _size["height"],
            width=_size["width"],
            height=_size["height"],
        )

    def get_monitor(self) -> Monitor | None:
        return self._monitor

    def text(self) -> str:
        return self._element.text

    def description(self) -> str:
        return str(self._element.get_attribute("content-desc"))

    def size(self) -> Size:
        return self._size

    def center(self) -> Point:
        return self._center

    def box(self) -> Box:
        return self._box

    def clear(self):
        self._element.clear()

    def input(self, text: str):
        self._element.send_keys(text)

    def tap(self):
        self._element.click()

    def long_press(self, duration: int = 2000):
        self._driver.tap([(self._center.x, self._center.y)], duration)

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
            element=self._element.find_element(parser.get_by(), parser.get_value()),
            language=language,
            timeout=self._timeout,
            monitor=self._monitor,
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
                monitor=self._monitor,
            )
            for ele in self._element.find_elements(parser.get_by(), parser.get_value())
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
        visible: bool,
        timeout: int = 15000,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> AndroidComponent | bool:
        if visible:
            if language is None:
                language = self._language
            parser = SelectorParser(selector, language, combination)
            wait = WebDriverWait(self._driver, timeout / 1000)
            ele = wait.until(
                EC.presence_of_element_located((parser.get_by(), parser.get_value()))
            )
            return AndroidComponent(
                driver=self._driver,
                element=ele,  # type: ignore
                language=language,
                timeout=timeout,
                monitor=self._monitor,
            )
        else:
            if language is None:
                language = self._language
            parser = SelectorParser(selector, language, combination)
            wait = WebDriverWait(self._driver, timeout / 1000)
            ele = wait.until_not(
                EC.presence_of_element_located((parser.get_by(), parser.get_value()))
            )
            return ele is None

    def get_attribute(self, name: str) -> str:
        return str(self._element.get_attribute(name))

    def is_displayed(self) -> bool:
        return self._element.is_displayed()

    def is_selected(self) -> bool:
        return self._element.is_selected()

    def is_enabled(self) -> bool:
        return self._element.is_enabled()

    def screenshot(self, path: Path | None = None) -> Path:
        if path is None:
            path = (
                config.CACHE_DIR
                / f"{self._name}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-screenshot.png"
            )
        self._element.screenshot(path)
        return path
