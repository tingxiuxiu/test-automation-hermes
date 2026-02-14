import time
import json
import threading

import elementpath
from xml.etree import ElementTree

from datetime import datetime
from pathlib import Path
from typing import Sequence
from loguru import logger

from .._core import config, portal_http
from ..protocol.component_protocol import ComponentProtocol
from ..protocol.driver_protocol import DriverProtocol
from ..protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..models.component import Bounds, Point, Size
from ..models.device import LocatorEngine
from ..models.media import ImageModal
from ..models.language import Language
from ..models.selector import Selector, SelectorKey, Window, Method
from .android_component import AndroidComponent
from .._media.image_component import ImageComponent
from .._media.image_calculate import find_all_templates
from .selector_to_xpath import SelectorToXpath
from .selector_to_jsonpath import SelectorToJsonpath


class AndroidDriver(DriverProtocol):
    def __init__(
        self,
        adb: DebugBridgeProtocol,
        tag: str,
        token: str,
        language: Language,
        locator_engine: LocatorEngine,
        timeout: int = 8000,
    ):
        self._adb = adb
        self._tag = tag
        self._language = language
        self._timeout = timeout
        self._window_size: Size | None = None
        self._token = token
        self._locator_engine = (
            SelectorToXpath
            if locator_engine == LocatorEngine.XPATH
            else SelectorToJsonpath
        )
        self._locator_engine_type = locator_engine
        self._headers = {"Authorization": f"Bearer {token}"}
        self._latest_page_id = -1
        self._cached_xml: dict[int, ElementTree.Element] = dict()
        self._cached_json: dict[int, dict] = dict()
        self._timer = threading.Timer(10, self._clear_cache)
        self._timer.start()
        self._clear_lock = threading.Lock()

    def close(self):
        with self._clear_lock:
            self._timer.cancel()

    def _clear_cache(self):
        with self._clear_lock:
            logger.debug("Clear cache")
            for k in self._cached_xml.keys():
                if k != self._latest_page_id:
                    del self._cached_xml[k]
            for k in self._cached_json.keys():
                if k != self._latest_page_id:
                    del self._cached_json[k]
            self._timer = threading.Timer(10, self._clear_cache)
            self._timer.start()

    def get_window_size(self, refresh: bool = False) -> Size:
        if refresh or not self._window_size:
            _size = self._adb.get_window_size()
            self._window_size = _size
        return self._window_size

    def get_xml_tree(self, display_id: int) -> str:
        xml_text = portal_http.get_hierarchy(display_id, "xml")
        return xml_text

    def get_json_tree(self, display_id: int) -> dict:
        json_obj = portal_http.get_hierarchy(display_id, "json")
        return json_obj

    def _wait_stable(self):
        start = time.time()
        while time.time() - start < 2:
            current_page_id = portal_http.get_state_id()

            if current_page_id == self._latest_page_id:
                break
            self._latest_page_id = current_page_id
            time.sleep(0.1)
        return self._latest_page_id

    def get_xml_element_tree(self, display_id: int) -> ElementTree.Element:
        self._wait_stable()
        if self._latest_page_id in self._cached_xml:
            return self._cached_xml[self._latest_page_id]
        else:
            xml_text = portal_http.get_hierarchy(display_id, "xml")
            self._cached_xml[self._latest_page_id] = ElementTree.XML(xml_text)
            return self._cached_xml[self._latest_page_id]

    def _find_nodes_by_xpath(
        self, xpath: str, visible: bool, window: Window, timeout: int
    ) -> Sequence[ElementTree.Element]:
        logger.debug(f"Find nodes by xpath: {xpath}")
        start_time = time.time()
        while time.time() - start_time < int(timeout / 1000):
            page = self.get_xml_element_tree(window.display_id)
            elements = elementpath.select(page, xpath)
            if elements:
                if visible:
                    return elements
            else:
                if not visible:
                    return []
        raise TimeoutError(f"Find nodes by xpath timeout: {xpath}")

    def _match_image(
        self,
        image: Path,
        threshold: float,
        visible: bool,
        timeout: int,
    ) -> Sequence[ImageModal]:
        tragets = []
        index = 0
        start_time = time.time()
        while time.time() - start_time < int(timeout / 1000):
            resource = self.screenshot()
            results = find_all_templates(resource, image, threshold)
            if results:
                if visible:
                    for item in results:
                        if item.confidence >= threshold:
                            tragets.append(
                                ImageModal(
                                    tag=f"{image.stem}_{index}",
                                    size=Size(
                                        width=item.bounds.right - item.bounds.left,
                                        height=item.bounds.bottom - item.bounds.top,
                                    ),
                                    center=Point(
                                        x=int(
                                            (item.bounds.left + item.bounds.right) / 2
                                        ),
                                        y=int(
                                            (item.bounds.top + item.bounds.bottom) / 2
                                        ),
                                    ),
                                    bounds=Bounds(
                                        left=item.bounds.left,
                                        top=item.bounds.top,
                                        right=item.bounds.right,
                                        bottom=item.bounds.bottom,
                                    ),
                                )
                            )
                            index += 1
                    return tragets
            else:
                if not visible:
                    return tragets
        raise TimeoutError("Match image timeout")

    def tap(self, target: ComponentProtocol | Selector | Point, wait_render: int = 500):
        """
        点击目标元素

        :param target: 目标元素，支持组件、选择器、坐标
        :param wait_render: 等待渲染时间，默认500ms
        """
        if isinstance(target, AndroidComponent):
            target.tap()
        elif isinstance(target, Selector):
            element = self.locator(target)
            if element:
                element.tap()
        elif isinstance(target, Point):
            portal_http.action_tap(0, target)
        else:
            raise ValueError("Invalid target type")
        time.sleep(wait_render / 1000)

    def long_press(
        self,
        target: ComponentProtocol | Selector | Point,
        duration: int = 1500,
        wait_render: int = 500,
    ):
        """
        长按目标元素

        :param target: 目标元素，支持组件、选择器、坐标
        :param duration: 长按时间，默认1500ms
        :param wait_render: 等待渲染时间，默认500ms
        """
        if isinstance(target, AndroidComponent):
            target.long_press(duration)
        elif isinstance(target, Selector):
            element = self.locator(target)
            if element:
                element.long_press(duration)
        elif isinstance(target, Point):
            portal_http.action_long_press(0, target, duration)
        else:
            raise ValueError("Invalid target type")
        time.sleep(wait_render / 1000)

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
        _engine = self._locator_engine(selector, language, combination)
        if _engine.get_method() == Method.XPATH:
            nodes = self._find_nodes_by_xpath(
                _engine.get_syntax(),
                visible=visible,
                window=_engine.get_window(),
                timeout=timeout or self._timeout,
            )
            if not nodes:
                return None
            return AndroidComponent(
                parent_syntax=_engine.get_syntax(),
                locator_engine=self._locator_engine_type,
                token=self._token,
                tag=self._tag,
                adb=self._adb,
                node=nodes[0],
                language=language,
                timeout=self._timeout,
                window=_engine.get_window(),
            )
        elif _engine.get_method() == Method.IMAGE:
            targets = self._match_image(
                _engine.get_image(),
                threshold=_engine.get_threshold(),
                visible=visible,
                timeout=timeout or self._timeout,
            )
            if not targets:
                return None
            return ImageComponent(
                image=targets[0],
                language=language,
                timeout=self._timeout,
                window=_engine.get_window(),
            )
        else:
            raise NotImplementedError(
                f"Locator engine {self._locator_engine_type} not implemented"
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
        _engine = self._locator_engine(selector, language, combination)
        if _engine.get_method() == Method.XPATH:
            nodes = self._find_nodes_by_xpath(
                _engine.get_syntax(),
                visible=visible,
                window=_engine.get_window(),
                timeout=timeout or self._timeout,
            )
            if not nodes:
                return []
            return [
                AndroidComponent(
                    parent_syntax=_engine.get_syntax(),
                    locator_engine=self._locator_engine_type,
                    token=self._token,
                    tag=self._tag,
                    adb=self._adb,
                    node=node,
                    language=language,
                    timeout=self._timeout,
                    window=_engine.get_window(),
                )
                for node in nodes
            ]
        elif _engine.get_method() == Method.IMAGE:
            targets = self._match_image(
                _engine.get_image(),
                threshold=_engine.get_threshold(),
                visible=visible,
                timeout=timeout or self._timeout,
            )
            if not targets:
                return []
            return [
                ImageComponent(
                    image=target,
                    language=language,
                    timeout=self._timeout,
                    window=_engine.get_window(),
                )
                for target in targets
            ]
        else:
            raise NotImplementedError(
                f"Locator engine {self._locator_engine_type} not implemented"
            )

    def scroll_into_view(
        self,
        target: Selector,
        scrollable: Selector | Bounds,
        *,
        display_id: int = 0,
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
            portal_http.action_swipe(0, start, end)
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
        display_id: int = 0,
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
        display_id: int = 0,
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
            portal_http.action_swipe(0, _start, _end, duration=duration)
            time.sleep(wait_render / 1000)

    def zoom_in(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        display_id: int = 0,
        scale: float = 0.5,
        duration: int = 500,
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
        portal_http.action_custom_zoom(
            display_id=display_id,
            start1=_target,
            end1=m_size,
            start2=m_size,
            end2=_target,
            duration=duration,
        )
        time.sleep(wait_render / 1000)

    def zoom_out(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        display_id: int = 0,
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
        portal_http.action_custom_zoom(
            display_id=display_id,
            start1=m_size,
            end1=_target,
            start2=_target,
            end2=m_size,
            duration=duration,
        )
        time.sleep(wait_render / 1000)

    def clear_text(self, display_id: int):
        portal_http.action_clear_text(display_id)

    def input_text(self, display_id: int, content: str):
        portal_http.action_input_text(display_id, content)

    def screenshot(self, path: Path | None = None, display_id: int = 0) -> Path:
        if path is None:
            path = (
                config.CACHE_DIR
                / f"{self._tag}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-screenshot.png"
            )
        content = portal_http.get_capture(display_id)
        with open(path, "wb") as f:
            f.write(content)
        return path
