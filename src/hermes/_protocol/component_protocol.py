from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol, overload

from ..models.component import Box, Point, Size
from ..models.language import Language
from ..models.selector import Monitor, Selector, SelectorKey


class ComponentProtocol(Protocol):
    def get_monitor(self) -> Monitor | None: ...

    def text(self) -> str: ...

    def description(self) -> str: ...

    def size(self) -> Size: ...

    def center(self) -> Point: ...

    def box(self) -> Box: ...

    def clear(self): ...

    def input(self, text: str): ...

    def tap(self): ...

    def long_press(self, duration: int = 2000): ...

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> ComponentProtocol: ...

    def locators(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]: ...

    @overload
    def wait_for(
        self,
        selector: Selector,
        *,
        visible: Literal[True],
        timeout: int = 8000,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> ComponentProtocol: ...

    @overload
    def wait_for(
        self,
        selector: Selector,
        *,
        visible: Literal[False],
        timeout: int = 8000,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> bool: ...

    def wait_for(
        self,
        selector: Selector,
        *,
        visible: bool,
        timeout: int = 8000,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> ComponentProtocol | bool: ...

    def get_attribute(self, name: str) -> str: ...

    def is_displayed(self) -> bool: ...

    def is_selected(self) -> bool: ...

    def is_enabled(self) -> bool: ...

    def screenshot(self, path: Path | None = None) -> Path: ...
