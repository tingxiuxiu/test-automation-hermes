from re import X
from typing import Sequence
from pathlib import Path

from ..models.language import Language
from ..models.selector import Selector, SelectorKey, Method
from ..protocol.selector_to_path_protocol import SelectorToPathProtocol

KEYS = [
    SelectorKey.ID,
    SelectorKey.TEXT,
    SelectorKey.DESCRIPTION,
    SelectorKey.XPATH,
    SelectorKey.CLASS_NAME,
    SelectorKey.TEXT_STARTS_WITH,
    SelectorKey.TEXT_ENDS_WITH,
    SelectorKey.TEXT_CONTAINS,
    SelectorKey.TEXT_MATCHES,
    SelectorKey.DESCRIPTION_STARTS_WITH,
    SelectorKey.DESCRIPTION_ENDS_WITH,
    SelectorKey.DESCRIPTION_CONTAINS,
    SelectorKey.DESCRIPTION_MATCHES,
    SelectorKey.IMAGE,
]


class SelectorToXpath(SelectorToPathProtocol):
    def __init__(
        self,
        selector: Selector,
        language: Language,
        combination: Sequence[SelectorKey] | None = None,
    ):
        self._selector = selector
        self._window = selector.window
        self._language = language
        self._combination = combination
        self._method: Method = Method.XPATH
        self._xpath: str | None = None
        self._image: Path | None = None
        self._threshold: float = 0.95
        self._inused_selector = self._valiadate_combination()
        self._process_selector()

    def get_window(self):
        return self._window

    def get_method(self):
        return self._method

    def get_syntax(self):
        if self._xpath is None:
            raise ValueError("Invalid xpath selector")
        return self._xpath

    def get_image(self):
        if self._image is None:
            raise ValueError("Invalid image selector")
        return self._image

    def get_threshold(self):
        return self._threshold

    def _valiadate_combination(self):
        inused_selector = {}
        if self._combination is None:
            for key in KEYS:
                if n := self._selector.get_value(key, self._language):
                    inused_selector[key] = n
                    break
        else:
            for key in self._combination:
                if key not in KEYS:
                    raise ValueError(f"Invalid selector key: {key}")
                if key == SelectorKey.IMAGE:
                    raise ValueError("Image selector is not supported in combination")
                if key == SelectorKey.XPATH:
                    raise ValueError("Xpath selector is not supported in combination")
                inused_selector[key] = self._selector.get_value(key, self._language)
        if not inused_selector:
            raise ValueError("Invalid selector: No valid selector found")
        return inused_selector

    def _process_selector(self):
        _values = []
        _xpath = "//*"
        # 单独处理 CLASS_NAME
        if SelectorKey.CLASS_NAME in self._inused_selector:
            _xpath = f"//{self._inused_selector[SelectorKey.CLASS_NAME]}"
            self._inused_selector.pop(SelectorKey.CLASS_NAME)
        for key, value in self._inused_selector.items():
            if key == SelectorKey.ID:
                _values.append(f'@resource-id="{value}"')
            elif key == SelectorKey.TEXT:
                _values.append(f'@text="{value}"')
            elif key == SelectorKey.DESCRIPTION:
                _values.append(f'@content-desc="{value}"')
            elif key == SelectorKey.XPATH:
                self._xpath = value
                self._method = Method.XPATH
                return
            elif key == SelectorKey.TEXT_STARTS_WITH:
                _values.append(f'starts-with(@text, "{value}")')
            elif key == SelectorKey.TEXT_ENDS_WITH:
                _values.append(f'ends-with(@text, "{value}")')
            elif key == SelectorKey.TEXT_CONTAINS:
                _values.append(f'contains(@text, "{value}")')
            elif key == SelectorKey.TEXT_MATCHES:
                _values.append(f'matches(@text, "{value}")')
            elif key == SelectorKey.DESCRIPTION_STARTS_WITH:
                _values.append(f'starts-with(@content-desc, "{value}")')
            elif key == SelectorKey.DESCRIPTION_ENDS_WITH:
                _values.append(f'ends-with(@content-desc, "{value}")')
            elif key == SelectorKey.DESCRIPTION_CONTAINS:
                _values.append(f'contains(@content-desc, "{value}")')
            elif key == SelectorKey.DESCRIPTION_MATCHES:
                _values.append(f'matches(@content-desc, "{value}")')
            elif key == SelectorKey.IMAGE:
                self._method = Method.IMAGE
                self._image = value.path
                self._threshold = value.threshold
                return
            else:
                raise ValueError(f"Invalid selector key: {key}")
        if _values:
            self._method = Method.XPATH
            self._xpath = _xpath + "[" + " and ".join(_values) + "]"
        else:
            if _xpath == "//*":
                raise ValueError("Invalid selector: No valid selector found")
            self._method = Method.XPATH
            self._xpath = _xpath
        return
