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
    """
    Represents an Android UI component with methods to interact with it.

    This class provides functionality to interact with Android UI components, including
    tapping, long-pressing, locating child components, and retrieving component properties.

    Attributes:
        _parent_syntax: Parent syntax of the component
        _locator_engine: Locator engine used for finding components
        _locator_engine_type: Type of locator engine (XPATH or JSONPATH)
        _token: Token for the component
        _tag: Tag for the component
        _adb: ADB interface for device communication
        _language: Language setting for the component
        _window: Window containing the component
        _timeout: Timeout for component operations
        _node: XML element representing the component
        _bounds: Bounds of the component
        _size: Size of the component
        _center: Center point of the component
    """

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
        Initialize an AndroidComponent instance.

        Args:
            node: XML element representing the component with attributes like text, resource-id, class, etc.
            parent_syntax: Parent syntax of the component
            locator_engine: Locator engine to use (XPATH or JSONPATH)
            token: Token for the component
            tag: Tag for the component
            adb: ADB interface for device communication
            language: Language setting for the component
            timeout: Timeout for component operations
            window: Window containing the component
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
        """
        Convert the bounds string from the component to a Bounds object.

        Returns:
            Bounds: A Bounds object representing the component's boundaries
        """
        _bounds = self._node.get("bounds", "0,0,0,0")
        left, top, right, bottom = _bounds.split(",")
        return Bounds(
            left=int(left),
            top=int(top),
            right=int(right),
            bottom=int(bottom),
        )

    def get_window(self) -> Window | None:
        """
        Get the window containing the component.

        Returns:
            Window | None: The window containing the component, or None if not available
        """
        return self._window

    def get_text(self) -> str | None:
        """
        Get the text of the component.

        Returns:
            str | None: The text of the component, or None if not available
        """
        return self._node.get("text")

    def get_description(self) -> str | None:
        """
        Get the content description of the component.

        Returns:
            str | None: The content description of the component, or None if not available
        """
        return self._node.get("content-desc")

    def get_size(self) -> Size:
        """
        Get the size of the component.

        Returns:
            Size: The size of the component
        """
        return self._size

    def get_center(self) -> Point:
        """
        Get the center point of the component.

        Returns:
            Point: The center point of the component
        """
        return self._center

    def get_bounds(self) -> Bounds:
        """
        Get the bounds of the component.

        Returns:
            Bounds: The bounds of the component
        """
        return self._bounds

    def tap(self, wait_render: int = 1000):
        """
        Tap on the component.

        Args:
            wait_render: Time to wait after tapping (in milliseconds)
        """
        portal_http.action_tap(self._window.display_id, self._center)
        time.sleep(wait_render / 1000)

    def long_press(self, duration: int = 2000, wait_render: int = 1000):
        """
        Long press on the component.

        Args:
            duration: Duration of the long press (in milliseconds)
            wait_render: Time to wait after long pressing (in milliseconds)
        """
        portal_http.action_long_press(
            self._window.display_id, self._center, duration=duration
        )
        time.sleep(wait_render / 1000)

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> "AndroidComponent":
        """
        Find a single child component matching the selector.

        Args:
            selector: Selector to match the component
            combination: Optional sequence of selector keys to combine
            language: Optional language setting for the selector

        Returns:
            AndroidComponent: The first matching component

        Raises:
            NotImplementedError: If the locator method is not implemented
            ValueError: If no elements match the selector
        """
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
        """
        Find all child components matching the selector.

        Args:
            selector: Selector to match the components
            combination: Optional sequence of selector keys to combine
            language: Optional language setting for the selector

        Returns:
            Sequence[AndroidComponent]: All matching components

        Raises:
            NotImplementedError: If the locator method is not implemented
            ValueError: If no elements match the selector
        """
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
        """
        Find child components matching the selector.

        Args:
            selector: Selector to match the components
            combination: Optional sequence of selector keys to combine
            language: Optional language setting for the selector

        Returns:
            Sequence[AndroidComponent]: All matching child components

        Raises:
            NotImplementedError: If the locator method is not implemented
            ValueError: If no elements match the selector
        """
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
        """
        Get an attribute of the component.

        Args:
            name: Name of the attribute to retrieve

        Returns:
            str | None: The value of the attribute, or None if not available
        """
        return self._node.get(name)

    def is_visible(self) -> bool:
        """
        Check if the component is visible.

        Returns:
            bool: True if the component is visible, False otherwise
        """
        return self._node.get("visible", "") == "true"

    def is_selected(self) -> bool:
        """
        Check if the component is selected.

        Returns:
            bool: True if the component is selected, False otherwise
        """
        return self._node.get("selected", "") == "true"

    def is_enabled(self) -> bool:
        """
        Check if the component is enabled.

        Returns:
            bool: True if the component is enabled, False otherwise
        """
        return self._node.get("enabled", "") == "true"

    def screenshot(self, path: Path | None = None) -> Path:
        """
        Take a screenshot of the component.

        Args:
            path: Optional path to save the screenshot

        Returns:
            Path: Path to the saved screenshot

        Raises:
            ValueError: If the screenshot cannot be read or cropped
        """
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
