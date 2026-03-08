from typing import Sequence
from pathlib import Path

from ..models.language import Language
from ..models.selector import Selector, SelectorKey, Method
from ..protocol.selector_to_path_protocol import SelectorToPathProtocol

KEYS = [
    SelectorKey.ID,
    SelectorKey.TEXT,
    SelectorKey.DESCRIPTION,
    SelectorKey.JSONPATH,
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


class SelectorToJsonpath(SelectorToPathProtocol):
    """
    Converts a Selector to JSONPath syntax for Android UI element lookup.

    This class implements the SelectorToPathProtocol to generate JSONPath
    expressions from selector criteria, supporting various matching strategies
    like exact matches, starts-with, ends-with, contains, and regex matches.
    """

    def __init__(
        self,
        selector: Selector,
        language: Language,
        combination: Sequence[SelectorKey] | None = None,
    ):
        """
        Initialize SelectorToJsonpath with selector criteria.

        Args:
            selector: Selector object containing UI element criteria
            language: Language for localization
            combination: Optional sequence of SelectorKey to use in combination
        """
        self._selector = selector
        self._window = selector.window
        self._language = language
        self._combination = combination
        self._method: Method = Method.JSONPATH
        self._jsonpath: str | None = None
        self._image: Path | None = None
        self._threshold: float = 0.95
        self._inused_selector = self._validate_combination()
        self._process_selector()

    def get_window(self):
        """
        Get the window associated with the selector.

        Returns:
            The window object from the selector
        """
        return self._window

    def get_method(self):
        """
        Get the method used for element lookup.

        Returns:
            Method enum value (JSONPATH or IMAGE)
        """
        return self._method

    def get_syntax(self):
        """
        Get the generated JSONPath syntax.

        Returns:
            str: JSONPath expression for element lookup

        Raises:
            ValueError: If JSONPath selector is invalid
        """
        if self._jsonpath is None:
            raise ValueError("Invalid jsonpath selector")
        return self._jsonpath

    def get_image(self):
        """
        Get the image path for image-based lookup.

        Returns:
            Path: Path to the image file

        Raises:
            ValueError: If image selector is invalid
        """
        if self._image is None:
            raise ValueError("Invalid image selector")
        return self._image

    def get_threshold(self):
        """
        Get the threshold for image matching.

        Returns:
            float: Threshold value (0.0-1.0)
        """
        return self._threshold

    def _validate_combination(self):
        """
        Validate and process the selector combination.

        Returns:
            dict: Dictionary of valid selector keys and values

        Raises:
            ValueError: If invalid selector key or no valid selector found
        """
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
                if key == SelectorKey.JSONPATH:
                    raise ValueError(
                        "Jsonpath selector is not supported in combination"
                    )
                inused_selector[key] = self._selector.get_value(key, self._language)
        if not inused_selector:
            raise ValueError("Invalid selector: No valid selector found")
        return inused_selector

    def _process_selector(self):
        """
        Process the selector to generate JSONPath syntax.

        Raises:
            ValueError: If invalid selector key or no valid selector found
        """
        _filters = []
        _base_path = "$[*]"
        if SelectorKey.CLASS_NAME in self._inused_selector:
            class_name = self._inused_selector[SelectorKey.CLASS_NAME]
            _filters.append(f'@.class == "{class_name}"')
            self._inused_selector.pop(SelectorKey.CLASS_NAME)
        for key, value in self._inused_selector.items():
            if key == SelectorKey.ID:
                _filters.append(f'@."resource-id" == "{value}"')
            elif key == SelectorKey.TEXT:
                _filters.append(f'@.text == "{value}"')
            elif key == SelectorKey.DESCRIPTION:
                _filters.append(f'@."content-desc" == "{value}"')
            elif key == SelectorKey.JSONPATH:
                self._jsonpath = value
                self._method = Method.JSONPATH
                return
            elif key == SelectorKey.TEXT_STARTS_WITH:
                _filters.append(f'starts_with(@.text, "{value}")')
            elif key == SelectorKey.TEXT_ENDS_WITH:
                _filters.append(f'ends_with(@.text, "{value}")')
            elif key == SelectorKey.TEXT_CONTAINS:
                _filters.append(f'contains(@.text, "{value}")')
            elif key == SelectorKey.TEXT_MATCHES:
                _filters.append(f'regex_test(@.text, "{value}")')
            elif key == SelectorKey.DESCRIPTION_STARTS_WITH:
                _filters.append(f'starts_with(@."content-desc", "{value}")')
            elif key == SelectorKey.DESCRIPTION_ENDS_WITH:
                _filters.append(f'ends_with(@."content-desc", "{value}")')
            elif key == SelectorKey.DESCRIPTION_CONTAINS:
                _filters.append(f'contains(@."content-desc", "{value}")')
            elif key == SelectorKey.DESCRIPTION_MATCHES:
                _filters.append(f'regex_test(@."content-desc", "{value}")')
            elif key == SelectorKey.IMAGE:
                self._method = Method.IMAGE
                self._image = value.path
                self._threshold = value.threshold
                return
            else:
                raise ValueError(f"Invalid selector key: {key}")
        if _filters:
            self._method = Method.JSONPATH
            filter_expr = " && ".join(_filters)
            self._jsonpath = f"{_base_path}[?({filter_expr})]"
        else:
            if _base_path == "$[*]":
                raise ValueError("Invalid selector: No valid selector found")
            self._method = Method.JSONPATH
            self._jsonpath = _base_path
        return
