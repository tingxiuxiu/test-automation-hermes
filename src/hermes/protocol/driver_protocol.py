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

    def get_page(self, display_id: int) -> str: ...

    def get_tree(self, display_id: int, timeout: int) -> ElementTree.Element: ...

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
        duration: int = 2000,
    ) -> None: ...

    def swipe(
        self,
        start: ComponentProtocol | Selector | Point,
        end: ComponentProtocol | Selector | Point,
        *,
        duration: int = 2000,
        repeat: int = 1,
        wait_render: int = 500,
    ) -> None: ...

    def zoom_in(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        scale: float = 0.5,
        duration: int = 500,
        wait_render: int = 500,
    ): ...

    def zoom_out(
        self,
        target: ComponentProtocol | Selector | Point,
        *,
        scale: float = 0.5,
        duration: int = 500,
        wait_render: int = 500,
    ): ...

    def screenshot(self, path: Path | None = None) -> Path: ...
