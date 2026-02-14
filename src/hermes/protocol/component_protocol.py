from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol, overload

from ..models.component import Bounds, Point, Size
from ..models.language import Language
from ..models.selector import Window, Selector, SelectorKey


class ComponentProtocol(Protocol):
    def get_window(self) -> Window | None: ...

    def get_text(self) -> str | None: ...

    def get_description(self) -> str | None: ...

    def get_size(self) -> Size: ...

    def get_center(self) -> Point: ...

    def get_bounds(self) -> Bounds: ...

    def tap(self): ...

    def long_press(self, duration: int = 2000): ...

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> "ComponentProtocol": ...

    def locators(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence["ComponentProtocol"]: ...

    def child(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence["ComponentProtocol"]: ...

    def get_attribute(self, name: str) -> str | None: ...

    def is_visible(self) -> bool: ...

    def is_selected(self) -> bool: ...

    def is_enabled(self) -> bool: ...

    def is_checked(self) -> bool: ...

    def screenshot(self, path: Path | None = None) -> Path: ...
