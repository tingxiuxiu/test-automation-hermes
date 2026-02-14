from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol, overload
from xml.etree import ElementTree
from ..models.component import Bounds, Point, Size
from ..models.language import Language
from ..models.selector import Selector, SelectorKey
from .component_protocol import ComponentProtocol


class DriverProtocol(Protocol):
    """驱动协议"""

    def close(self): ...

    def get_xml_tree(self, display_id: int) -> str: ...

    def get_json_tree(self, display_id: int) -> dict: ...

    def get_xml_element_tree(self, display_id: int) -> ElementTree.Element: ...

    def get_window_size(self) -> Size: ...

    def tap(self, target: ComponentProtocol | Selector | Point): ...

    def long_press(
        self, target: ComponentProtocol | Selector | Point, duration: int = 2000
    ): ...

    def locator(
        self,
        selector: Selector,
        *,
        visible: bool = True,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> ComponentProtocol | None: ...

    def locators(
        self,
        selector: Selector,
        *,
        visible: bool = True,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]: ...

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
    ) -> ComponentProtocol | None: ...

    def drag_and_drop(
        self,
        start: ComponentProtocol | Selector | Point,
        end: ComponentProtocol | Selector | Point,
        *,
        display_id: int = 0,
        duration: int = 2000,
    ) -> None: ...

    def swipe(
        self,
        start: ComponentProtocol | Selector | Point,
        end: ComponentProtocol | Selector | Point,
        *,
        display_id: int = 0,
        duration: int = 2000,
        repeat: int = 1,
        wait_render: int = 500,
    ) -> None: ...

    def zoom_in(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        display_id: int = 0,
        scale: float = 0.5,
        duration: int = 500,
        wait_render: int = 500,
    ): ...

    def zoom_out(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        display_id: int = 0,
        scale: float = 0.5,
        duration: int = 500,
        wait_render: int = 500,
    ): ...

    def clear_text(self, display_id: int): ...

    def input_text(self, display_id: int, content: str): ...

    def screenshot(self, path: Path | None = None, display_id: int = 0) -> Path: ...
