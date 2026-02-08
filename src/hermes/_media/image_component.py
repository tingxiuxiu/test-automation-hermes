from collections.abc import Sequence
from pathlib import Path

from ..models.component import Bounds, Point, Size
from ..models.language import Language
from ..models.media import ImageModal
from ..models.selector import Selector, SelectorKey, Window
from ..protocol.component_protocol import ComponentProtocol


class ImageComponent(ComponentProtocol):
    def __init__(
        self,
        image: ImageModal,
        language: Language,
        timeout: float,
        window: Window,
    ):
        self._image = image
        self._language = language
        self._timeout = timeout
        self._window = window

    def get_window(self) -> Window | None:
        return self._window

    def get_text(self) -> str:
        raise NotImplementedError

    def get_description(self) -> str:
        raise NotImplementedError

    def get_size(self) -> Size:
        return self._image.size

    def get_center(self) -> Point:
        return self._image.center

    def get_bounds(self) -> Bounds:
        return self._image.bounds

    def clear(self):
        raise NotImplementedError

    def input(self, text: str):
        raise NotImplementedError

    def tap(self):
        raise NotImplementedError

    def long_press(self, duration: int = 2000):
        raise NotImplementedError

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> ComponentProtocol:
        raise NotImplementedError

    def locators(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]:
        raise NotImplementedError

    def child(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]:
        raise NotImplementedError

    def children(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]:
        raise NotImplementedError

    def get_attribute(self, name: str) -> str:
        raise NotImplementedError

    def is_visible(self) -> bool:
        raise NotImplementedError

    def is_selected(self) -> bool:
        raise NotImplementedError

    def is_enabled(self) -> bool:
        raise NotImplementedError

    def is_checked(self) -> bool:
        raise NotImplementedError

    def screenshot(self, path: Path | None = None) -> Path:
        raise NotImplementedError
