import time

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import elementpath
import cv2

from xml.etree import ElementTree

from ..models.language import Language
from .._core import config, portal_http
from .._core.portal_protocol import PortalHTTP
from ..protocol.component_protocol import ComponentProtocol
from ..protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..models.device import LocatorEngine
from ..models.component import Bounds, Point, Size
from ..models.selector import Window, Selector, SelectorKey, Method
from .selector_to_jsonpath import SelectorToJsonpath
from .selector_to_xpath import SelectorToXpath


class AndroidComponent(ComponentProtocol):
    def __init__(
        self,
        node: ElementTree.Element,
        parent_syntax: str,
        locator_engine: LocatorEngine,
        token: str,
        tag: str,
        adb: DebugBridgeProtocol,
        language: Language,
        timeout: int,
        window: Window,
    ):
        """
        node: attribute of the component
            index: index of the component
            text: text of the component
            resource-id: resource-id of the component
            class: class of the component
            package: package of the component
            content-desc: content-desc of the component
            checkable: checkable of the component
            checked: checked of the component
            clickable: clickable of the component
            enabled: enabled of the component
            focusable: focusable of the component
            focused: focused of the component
            scrollable: scrollable of the component
            long-clickable: long-clickable of the component
            password: password of the component
            selected: selected of the component
            drawing-order: drawing-order of the component
            bounds: bounds of the component "0,0,0,0"
        parent_syntax: parent syntax of the component
        token: token of the component
        tag: tag of the component
        language: language of the component
        timeout: timeout of the component
        window: window of the component
        """
        self._parent_syntax = parent_syntax
        self._locator_engine = (
            SelectorToXpath
            if locator_engine == LocatorEngine.XPATH
            else SelectorToJsonpath
        )
        self._locator_engine_type = locator_engine
        self._token = token
        self._tag = tag
        self._adb = adb
        self._language = language
        self._window = window
        self._timeout = timeout
        self._node = node
        self._bounds = self._convert_bounds()
        self._size = Size(
            width=self._bounds.right - self._bounds.left,
            height=self._bounds.bottom - self._bounds.top,
        )
        self._center = Point(
            x=int(self._bounds.left + self._size.width / 2),
            y=int(self._bounds.top + self._size.height / 2),
        )

    def _convert_bounds(self) -> Bounds:
        _bounds = self._node.get("bounds", "0,0,0,0")
        left, top, right, bottom = _bounds.split(",")
        return Bounds(
            left=int(left),
            top=int(top),
            right=int(right),
            bottom=int(bottom),
        )

    def get_window(self) -> Window | None:
        return self._window

    def get_text(self) -> str | None:
        return self._node.get("text")

    def get_description(self) -> str | None:
        return self._node.get("content-desc")

    def get_size(self) -> Size:
        return self._size

    def get_center(self) -> Point:
        return self._center

    def get_bounds(self) -> Bounds:
        return self._bounds

    def tap(self):
        portal_http.action_tap(self._window.display_id, self._center)
        time.sleep(0.2)

    def long_press(self, duration: int = 2000):
        portal_http.action_long_press(
            self._window.display_id, self._center, duration=duration
        )
        time.sleep(0.2)

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> "AndroidComponent":
        if language is None:
            language = self._language
        _engine = self._locator_engine(selector, language, combination)
        if _engine.get_method() == Method.IMAGE:
            raise NotImplementedError("Image is not implemented")
        elif _engine.get_method() == Method.XPATH:
            elements = elementpath.select(self._node, _engine.get_syntax())
            if not elements:
                raise ValueError(f"Invalid {_engine.get_method().value} selector")
            return AndroidComponent(
                node=elements[0],
                parent_syntax=self._parent_syntax,
                locator_engine=self._locator_engine_type,
                token=self._token,
                tag=self._tag,
                adb=self._adb,
                language=language,
                timeout=self._timeout,
                window=self._window,
            )
        else:
            raise NotImplementedError(
                f"Locator engine {_engine.get_method().value} is not implemented"
            )

    def locators(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence["AndroidComponent"]:
        if language is None:
            language = self._language
        _engine = self._locator_engine(selector, language, combination)
        if _engine.get_method() == Method.IMAGE:
            raise NotImplementedError("Image is not implemented")
        elif _engine.get_method() == Method.XPATH:
            elements = elementpath.select(self._node, _engine.get_syntax())
            if not elements:
                raise ValueError(f"Invalid {_engine.get_method().value} selector")
            return [
                AndroidComponent(
                    node=ele,
                    parent_syntax=self._parent_syntax,
                    locator_engine=self._locator_engine_type,
                    token=self._token,
                    tag=self._tag,
                    adb=self._adb,
                    language=language,
                    timeout=self._timeout,
                    window=self._window,
                )
                for ele in elements
            ]
        else:
            raise NotImplementedError(
                f"Locator engine {_engine.get_method().value} is not implemented"
            )

    def child(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence["AndroidComponent"]:
        if language is None:
            language = self._language
        _engine = self._locator_engine(selector, language, combination)
        if _engine.get_method() == Method.IMAGE:
            raise NotImplementedError("Image is not implemented")
        elif _engine.get_method() == Method.XPATH:
            elements = elementpath.select(self._node, _engine.get_syntax())
            if not elements:
                raise ValueError(f"Invalid {_engine.get_method().value} selector")
            return [
                AndroidComponent(
                    node=ele,
                    parent_syntax=self._parent_syntax,
                    locator_engine=self._locator_engine_type,
                    token=self._token,
                    tag=self._tag,
                    adb=self._adb,
                    language=language,
                    timeout=self._timeout,
                    window=self._window,
                )
                for ele in elements
            ]
        else:
            raise NotImplementedError(
                f"Locator engine {_engine.get_method().value} is not implemented"
            )

    def get_attribute(self, name: str) -> str | None:
        return self._node.get(name)

    def is_visible(self) -> bool:
        return self._node.get("visible", "") == "true"

    def is_selected(self) -> bool:
        return self._node.get("selected", "") == "true"

    def is_enabled(self) -> bool:
        return self._node.get("enabled", "") == "true"

    def is_checked(self) -> bool:
        return self._node.get("checked", "") == "true"

    def screenshot(self, path: Path | None = None) -> Path:
        if path is None:
            path = (
                config.CACHE_DIR
                / f"{self._tag}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-screenshot.png"
            )
        content = portal_http.get_capture(self._window.display_id)
        with open(path, "wb") as f:
            f.write(content)
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError("Failed to read screenshot")
        cropped = img[
            self._bounds.top : self._bounds.bottom,
            self._bounds.left : self._bounds.right,
        ]
        if cropped is None:
            raise ValueError("Failed to crop screenshot")
        cv2.imwrite(str(path), cropped)
        return path
