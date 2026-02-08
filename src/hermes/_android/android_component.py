from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import httpx
import elementpath
import cv2

from xml.etree import ElementTree

from ..models.language import Language
from .._core import config
from .._core.portal_protocol import PortalHTTP
from ..protocol.component_protocol import ComponentProtocol
from ..protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..models.component import Bounds, Point, Size
from ..models.selector import Window, Selector, SelectorKey
from .selector_paser import SelectorParser, Method


class AndroidComponent(ComponentProtocol):
    def __init__(
        self,
        node: ElementTree.Element,
        base_xpath: str,
        base_url: str,
        token: str,
        tag: str,
        adb: DebugBridgeProtocol,
        client: httpx.Client,
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
        base_xpath: base xpath of the component
        base_url: base url of the component
        token: token of the component
        tag: tag of the component
        client: client of the component
        language: language of the component
        timeout: timeout of the component
        window: window of the component
        """
        self._base_url = base_url
        self._base_xpath = base_xpath
        self._token = token
        self._tag = tag
        self._adb = adb
        self._language = language
        self._window = window
        self._timeout = timeout
        self._node = node
        self._client = client
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

    def clear(self):
        response = self._client.post(
            f"{self._base_url}{PortalHTTP.INPUT_CLEAR}",
            json={
                "displayId": self._window.display_id,
            },
        )
        response.raise_for_status()

    def input(self, text: str):
        response = self._client.post(
            f"{self._base_url}{PortalHTTP.INPUT_TEXT}",
            json={
                "displayId": self._window.display_id,
                "text": text,
            },
        )
        response.raise_for_status()

    def tap(self):
        self._adb.tap(self._center.x, self._center.y)

    def long_press(self, duration: int = 2000):
        self._adb.long_press(self._center.x, self._center.y, duration=duration)

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> "AndroidComponent":
        if language is None:
            language = self._language
        parser = SelectorParser(selector, language, combination)
        if parser.get_method() == Method.IMAGE:
            raise NotImplementedError("Image is not implemented")
        else:
            elements = elementpath.select(self._node, parser.get_xpath())
            if not elements:
                raise ValueError("Invalid xpath selector")
            return AndroidComponent(
                node=elements[0],
                base_xpath=self._base_xpath,
                base_url=self._base_url,
                token=self._token,
                tag=self._tag,
                adb=self._adb,
                client=self._client,
                language=language,
                timeout=self._timeout,
                window=self._window,
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
        parser = SelectorParser(selector, language, combination)
        if parser.get_method() == Method.IMAGE:
            raise NotImplementedError("Image is not implemented")
        else:
            elements = elementpath.select(self._node, parser.get_xpath())
            if not elements:
                raise ValueError("Invalid xpath selector")
            return [
                AndroidComponent(
                    node=ele,
                    base_xpath=self._base_xpath,
                    base_url=self._base_url,
                    token=self._token,
                    tag=self._tag,
                    adb=self._adb,
                    client=self._client,
                    language=language,
                    timeout=self._timeout,
                    window=self._window,
                )
                for ele in elements
            ]

    def child(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence["AndroidComponent"]:
        if language is None:
            language = self._language
        parser = SelectorParser(selector, language, combination)
        if parser.get_method() == Method.IMAGE:
            raise NotImplementedError("Image is not implemented")
        elements = elementpath.select(self._node, parser.get_xpath())
        if not elements:
            raise ValueError("Invalid xpath selector")
        return [
            AndroidComponent(
                node=ele,
                base_xpath=self._base_xpath,
                base_url=self._base_url,
                token=self._token,
                tag=self._tag,
                adb=self._adb,
                client=self._client,
                language=language,
                timeout=self._timeout,
                window=self._window,
            )
            for ele in elements
        ]

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
