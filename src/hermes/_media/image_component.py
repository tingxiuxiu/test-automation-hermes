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
        raise NotImplementedError("Image component does not support text")

    def get_description(self) -> str:
        raise NotImplementedError("Image component does not support description")

    def get_size(self) -> Size:
        return self._image.size

    def get_center(self) -> Point:
        return self._image.center

    def get_bounds(self) -> Bounds:
        return self._image.bounds

    def clear_text(self):
        raise NotImplementedError("Image component does not support clear text")

    def input_text(self, content: str):
        raise NotImplementedError("Image component does not support input text")

    def tap(self):
        raise NotImplementedError("Image component does not support tap")

    def long_press(self, duration: int = 2000):
        raise NotImplementedError("Image component does not support long press")

    def locator(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> ComponentProtocol:
        raise NotImplementedError("Image component does not support locator")

    def locators(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]:
        raise NotImplementedError("Image component does not support locators")

    def child(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]:
        raise NotImplementedError("Image component does not support child")

    def children(
        self,
        selector: Selector,
        *,
        combination: Sequence[SelectorKey] | None = None,
        language: Language | None = None,
    ) -> Sequence[ComponentProtocol]:
        raise NotImplementedError("Image component does not support children")

    def get_attribute(self, name: str) -> str:
        raise NotImplementedError("Image component does not support attribute")

    def is_visible(self) -> bool:
        raise NotImplementedError("Image component does not support visible")

    def is_selected(self) -> bool:
        raise NotImplementedError("Image component does not support selected")

    def is_enabled(self) -> bool:
        raise NotImplementedError("Image component does not support enabled")

    def is_checked(self) -> bool:
        raise NotImplementedError("Image component does not support checked")

    def screenshot(self, path: Path | None = None) -> Path:
        raise NotImplementedError("Image component does not support screenshot")
