import time
import json
import httpx

import elementpath
from xml.etree import ElementTree

from datetime import datetime
from pathlib import Path
from typing import Literal, overload, Sequence
from loguru import logger

from .._core import config, hermes_cache
from .._core.portal_protocol import PortalHTTP
from ..protocol.component_protocol import ComponentProtocol
from ..protocol.driver_protocol import DriverProtocol
from ..protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..models.component import Bounds, Point, Size
from ..models.language import Language
from ..models.selector import Selector, SelectorKey, Window
from .android_component import AndroidComponent
from .._media.image_component import ImageComponent
from .selector_paser import SelectorParser, Method
from ..utils.tools import parse_url
from .._media.image_calc import ImageCalc


class AndroidDriver(DriverProtocol):
    def __init__(
        self,
        adb: DebugBridgeProtocol,
        tag: str,
        base_url: str,
        token: str,
        client: httpx.Client,
        language: Language,
        timeout: int = 8000,
    ):
        self._adb = adb
        self._tag = tag
        self._language = language
        self._timeout = timeout
        self._window_size: Size | None = None
        self._base_url = base_url
        self._token = token
        self._client = client
        self._headers = {"Authorization": f"Bearer {token}"}
        self._latest_page_id = -1
        self._cached_page: dict[int, ElementTree.Element] = dict()

    def get_window_size(self, refresh: bool = False) -> Size:
        if refresh or not self._window_size:
            _size = self._adb.get_window_size()
            self._window_size = _size
        return self._window_size

    def get_page(self, display_id: int) -> str:
        latest_page_id = self._wait_stable(self._timeout)
        response = self._client.get(
            parse_url(self._base_url, f"{PortalHTTP.NODES_XML}/{display_id}")
        )
        if response.status_code == 200:
            raw_bytes = response.content
            if not raw_bytes:
                raise ValueError("Empty response content")
            xml_text = raw_bytes.decode("utf-8")
            self._cached_page[latest_page_id] = ElementTree.XML(xml_text)
            return xml_text
        raise ValueError(f"Failed to get page, error: {response.content}")

    def get_json_tree(self, display_id: int) -> dict:
        self._wait_stable(self._timeout)
        response = self._client.get(
            parse_url(self._base_url, f"{PortalHTTP.NODES_XML}/{display_id}")
        )
        if response.status_code == 200:
            raw_bytes = response.content
            if not raw_bytes:
                raise ValueError("Empty response content")
            json_text = raw_bytes.decode("utf-8")
            return json.loads(json_text)
        raise ValueError(f"Failed to get page, error: {response.content}")

    def _wait_stable(self, timeout: int):
        start = time.time()
        while time.time() - start < timeout / 1000:
            response = self._client.get(
                parse_url(self._base_url, PortalHTTP.WINDOW_STATE)
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to get status, error: {response.content}")
            res_json = response.json()
            if not res_json.get("success"):
                raise ValueError(
                    f"Failed to get status, error: {res_json.get('result')}"
                )
            else:
                current_page_id = res_json.get("result")["stateId"]
                if current_page_id == self._latest_page_id:
                    break
                self._latest_page_id = current_page_id
                time.sleep(0.1)
        return self._latest_page_id

    def get_tree(self, display_id: int, timeout: int) -> ElementTree.Element:
        latest_page_id = self._wait_stable(timeout)
        if latest_page_id in self._cached_page:
            return self._cached_page[latest_page_id]
        else:
            response = self._client.get(
                parse_url(self._base_url, f"{PortalHTTP.NODES_XML}/{display_id}")
            )
            response.raise_for_status()
            raw_bytes = response.content
            if not raw_bytes:
                raise ValueError("Empty response content")
            xml_text = raw_bytes.decode("utf-8")
            self._cached_page[latest_page_id] = ElementTree.XML(xml_text)
            return self._cached_page[latest_page_id]

    def _find_nodes_by_xpath(
        self, xpath: str, visible: bool, window: Window, timeout: int
    ) -> Sequence[ElementTree.Element]:
        logger.debug(f"Find nodes by xpath: {xpath}")
        start_time = time.time()
        while time.time() - start_time < int(timeout / 1000):
            page = self.get_tree(window.display_id, timeout)
            elements = elementpath.select(page, xpath)
            if elements:
                if visible:
                    return elements
            else:
                if not visible:
                    return []
        raise TimeoutError("Check nodes timeout")

    def tap(self, target: ComponentProtocol | Selector | Point):
        if isinstance(target, AndroidComponent):
            target.tap()
        elif isinstance(target, Selector):
            element = self.locator(target)
            if element:
                element.tap()
        elif isinstance(target, Point):
            self._adb.tap(target.x, target.y)
        else:
            raise ValueError("Invalid target type")

    def long_press(
        self, target: ComponentProtocol | Selector | Point, duration: int = 2000
    ):
        if isinstance(target, AndroidComponent):
            target.long_press(duration)
        elif isinstance(target, Selector):
            element = self.locator(target)
            if element:
                element.long_press(duration)
        elif isinstance(target, Point):
            self._adb.long_press(target.x, target.y, duration)
        else:
            raise ValueError("Invalid target type")

    def locator(
        self,
        selector: Selector,
        *,
        visible: bool = True,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
        timeout: int | None = None,
    ) -> ComponentProtocol | None:
        if language is None:
            language = self._language
        parser = SelectorParser(selector, language, combination)
        if parser.get_method() == Method.IMAGE:
            img_modals = ImageCalc().wait_for(
                parser.get_image(),
                driver=self,
                threshold=parser.get_threshold(),
                visible=visible,
                timeout=timeout or self._timeout,
            )
            if not img_modals:
                return None
            return ImageComponent(
                image=img_modals[0],
                language=language,
                timeout=self._timeout,
                window=parser.get_window(),
            )
        else:
            nodes = self._find_nodes_by_xpath(
                parser.get_xpath(),
                visible=visible,
                window=parser.get_window(),
                timeout=timeout or self._timeout,
            )
            if not nodes:
                return None
            return AndroidComponent(
                base_url=self._base_url,
                base_xpath=parser.get_xpath(),
                token=self._token,
                tag=self._tag,
                adb=self._adb,
                client=self._client,
                node=nodes[0],
                language=language,
                timeout=self._timeout,
                window=parser.get_window(),
            )

    def locators(
        self,
        selector: Selector,
        *,
        visible: bool = True,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
        timeout: int | None = None,
    ) -> Sequence[ComponentProtocol]:
        if language is None:
            language = self._language
        parser = SelectorParser(selector, language, combination)
        if parser.get_method() == Method.IMAGE:
            img_modals = ImageCalc().wait_for(
                parser.get_image(),
                driver=self,
                threshold=parser.get_threshold(),
                visible=visible,
                timeout=timeout or self._timeout,
            )
            if not img_modals:
                return []
            return [
                ImageComponent(
                    image=img_modal,
                    language=language,
                    timeout=self._timeout,
                    window=parser.get_window(),
                )
                for img_modal in img_modals
            ]
        else:
            nodes = self._find_nodes_by_xpath(
                parser.get_xpath(),
                visible=visible,
                window=parser.get_window(),
                timeout=timeout or self._timeout,
            )
            if not nodes:
                return []
            return [
                AndroidComponent(
                    base_url=self._base_url,
                    base_xpath=parser.get_xpath(),
                    token=self._token,
                    tag=self._tag,
                    adb=self._adb,
                    client=self._client,
                    node=node,
                    language=language,
                    timeout=self._timeout,
                    window=parser.get_window(),
                )
                for node in nodes
            ]

    def scroll_into_view(
        self,
        target: Selector,
        scrollable: Selector | Bounds,
        *,
        horizontal: bool = False,
        target_combination: Sequence[SelectorKey] | None = None,
        scrollable_combination: Sequence[SelectorKey] | None = None,
        target_language: Language | None = None,
        scrollable_language: Language | None = None,
    ) -> ComponentProtocol | None:
        if target_language is None:
            target_language = self._language
        if scrollable_language is None:
            scrollable_language = self._language
        target_s = SelectorParser(target, target_language, target_combination)
        if isinstance(scrollable, Bounds):
            if horizontal:
                start = Point(
                    x=int(scrollable.left + (scrollable.right - scrollable.left) / 2),
                    y=int(scrollable.top + (scrollable.bottom - scrollable.top) / 2),
                )
                end = Point(
                    x=int(scrollable.left + (scrollable.right - scrollable.left) / 2),
                    y=int(
                        scrollable.bottom * 0.7
                        + (scrollable.bottom - scrollable.top) / 2
                    ),
                )
            else:
                start = Point(
                    x=int(scrollable.left + (scrollable.right - scrollable.left) / 2),
                    y=int(scrollable.top + (scrollable.bottom - scrollable.top) / 2),
                )
                end = Point(
                    x=int(scrollable.left + (scrollable.right - scrollable.left) / 2),
                    y=int(
                        scrollable.top * 0.3 + (scrollable.bottom - scrollable.top) / 2
                    ),
                )
        else:
            scrollable_element = self.locator(
                scrollable,
                visible=True,
                combination=scrollable_combination,
                language=scrollable_language,
                timeout=1000,
            )
            if not scrollable_element:
                return None
            if horizontal:
                start = Point(
                    x=int(
                        scrollable_element.get_bounds().left
                        + (
                            scrollable_element.get_bounds().right
                            - scrollable_element.get_bounds().left
                        )
                        / 2
                    ),
                    y=int(
                        scrollable_element.get_bounds().top
                        + (
                            scrollable_element.get_bounds().bottom
                            - scrollable_element.get_bounds().top
                        )
                        / 2
                    ),
                )
                end = Point(
                    x=int(
                        scrollable_element.get_bounds().left
                        + (
                            scrollable_element.get_bounds().right
                            - scrollable_element.get_bounds().left
                        )
                        / 2
                    ),
                    y=int(
                        scrollable_element.get_bounds().bottom * 0.7
                        + (
                            scrollable_element.get_bounds().bottom
                            - scrollable_element.get_bounds().top
                        )
                        / 2
                    ),
                )
            else:
                start = Point(
                    x=int(
                        scrollable_element.get_bounds().left
                        + (
                            scrollable_element.get_bounds().right
                            - scrollable_element.get_bounds().left
                        )
                        / 2
                    ),
                    y=int(
                        scrollable_element.get_bounds().top
                        + (
                            scrollable_element.get_bounds().bottom
                            - scrollable_element.get_bounds().top
                        )
                        / 2
                    ),
                )
                end = Point(
                    x=int(
                        scrollable_element.get_bounds().left
                        + (
                            scrollable_element.get_bounds().right
                            - scrollable_element.get_bounds().left
                        )
                        / 2
                    ),
                    y=int(
                        scrollable_element.get_bounds().top * 0.3
                        + (
                            scrollable_element.get_bounds().bottom
                            - scrollable_element.get_bounds().top
                        )
                        / 2
                    ),
                )
        for _ in range(8):
            self.swipe(start, end, wait_render=500)
            return self.locator(
                target,
                visible=True,
                combination=target_combination,
                language=target_language,
                timeout=1000,
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
            _start = self.locator(start, visible=True)
            if not _start:
                return None
            _start = _start.get_center()
        else:
            _start = start.get_center()

        if isinstance(end, Point):
            _end = end
        elif isinstance(end, Selector):
            _end = self.locator(end, visible=True)
            if not _end:
                return None
            _end = _end.get_center()
        else:
            _end = end.get_center()
        self._adb.drag_and_drop(_start, _end, duration=duration)

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
            _start = self.locator(start, visible=True)
            if not _start:
                return None
            _start = _start.get_center()
        else:
            _start = start.get_center()

        if isinstance(end, Point):
            _end = end
        elif isinstance(end, Selector):
            _end = self.locator(end, visible=True)
            if not _end:
                return None
            _end = _end.get_center()
        else:
            _end = end.get_center()
        for _ in range(repeat):
            self._adb.swipe(_start, _end, duration=duration)
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
            _target = self.locator(target, visible=True)
            if not _target:
                return None
            _target = _target.get_center()
        else:
            _target = target.get_center()
        w_size = self.get_window_size()
        m_size = Point(
            x=int(w_size.width / 2 * scale), y=int(w_size.height / 2 * scale)
        )
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
            _target = self.locator(target, visible=True)
            if not _target:
                return None
            _target = _target.get_center()
        else:
            _target = target.get_center()
        w_size = self.get_window_size()
        m_size = Point(
            x=int(w_size.width / 2 * scale), y=int(w_size.height / 2 * scale)
        )
        time.sleep(wait_render / 1000)

    def screenshot(self, path: Path | None = None, display_id: int = 0) -> Path:
        if path is None:
            path = (
                config.CACHE_DIR
                / f"{self._tag}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-screenshot.png"
            )
        res = self._client.get(f"{self._base_url}{PortalHTTP.SCREENSHOT}/{display_id}")
        if res.status_code == 200:
            with open(path, "wb") as f:
                f.write(res.content)
        return path
