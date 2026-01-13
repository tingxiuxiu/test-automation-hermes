from collections.abc import Sequence

from appium.webdriver.common.appiumby import AppiumBy

from ..models.language import Language
from ..models.selector import Selector, SelectorKey

_UIAUTOMATOR_FORMAT = {
    "id": 'new UiSelector().resourceId("{}")',
    "class_name": 'new UiSelector().className("{}")',
    "description": 'new UiSelector().description("{}")',
    "description_contains": 'new UiSelector().descriptionContains("{}")',
    "description_starts_with": 'new UiSelector().descriptionStartsWith("{}")',
    "description_matches": 'new UiSelector().descriptionMatches("{}")',
    "text": 'new UiSelector().text("{}")',
    "text_contains": 'new UiSelector().textContains("{}")',
    "text_starts_with": 'new UiSelector().textStartsWith("{}")',
    "text_matches": 'new UiSelector().textMatches("{}")',
}


class SelectorParser:
    def __init__(
        self,
        selector: Selector,
        language: Language,
        combination: Sequence[SelectorKey] | None = None,
    ):
        self._selector = selector.to_dict()
        self._monitor = selector.monitor
        self._language = language
        self._combination = combination
        self._by = None
        self._value = None
        self._inused_selector = self._valiadate_combination()
        self._filter_selector()

    def get_monitor(self):
        return self._monitor

    def get_by(self):
        if self._by is None:
            raise ValueError("Invalid selector")
        return self._by

    def get_value(self):
        if self._value is None:
            raise ValueError("Invalid selector")
        return self._value

    def _transform_ends_with(self, value):
        if isinstance(value, str):
            return f".*{value}"
        else:
            return f".*{value[self._language]}"

    def _valiadate_combination(self):
        inused_selector = {}
        if self._combination is None:
            for key in self._selector:
                if not self._selector[key]:
                    if key == SelectorKey.TEXT_ENDS_WITH.value:
                        inused_selector[SelectorKey.TEXT_MATCHES.value] = (
                            self._transform_ends_with(self._selector[key])
                        )
                    elif key == SelectorKey.DESCRIPTION_ENDS_WITH.value:
                        inused_selector[SelectorKey.DESCRIPTION_MATCHES.value] = (
                            self._transform_ends_with(self._selector[key])
                        )
                    else:
                        inused_selector[key] = self._transform_value(
                            self._selector[key]
                        )
                    break
            if not inused_selector:
                raise ValueError("Invalid selector")
        else:
            for key in self._combination:
                if key not in self._selector:
                    raise ValueError(f"Invalid selector key: {key}")
                else:
                    inused_selector[key] = self._transform_value(
                        self._selector[key.value]
                    )
                if key == SelectorKey.IMAGE:
                    raise ValueError("Image selector is not supported in combination")
                elif key == SelectorKey.ANDROID_UIAUTOMATOR:
                    raise ValueError(
                        "Android uiautomator selector is not supported in combination"
                    )
                elif key == SelectorKey.XPATH:
                    raise ValueError("Xpath selector is not supported in combination")
        return inused_selector

    def _transform_value(self, value):
        if isinstance(value, str):
            return value
        else:
            return value[self._language]

    def _filter_selector(self):
        for key, value in self._inused_selector.items():
            if key == SelectorKey.ID.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.TEXT.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.DESCRIPTION.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.XPATH.value:
                self._by = AppiumBy.XPATH
                self._value = value
            elif key == SelectorKey.TEXT_STARTS_WITH.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.TEXT_CONTAINS.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.TEXT_MATCHES.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.DESCRIPTION_STARTS_WITH.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.DESCRIPTION_CONTAINS.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.DESCRIPTION_MATCHES.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.ANDROID_UIAUTOMATOR.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = value
            elif key == SelectorKey.CLASS_NAME.value:
                self._by = AppiumBy.ANDROID_UIAUTOMATOR
                self._value = _UIAUTOMATOR_FORMAT[key].format(value)
            elif key == SelectorKey.IMAGE.value:
                self._by = AppiumBy.IMAGE
                self._value = value
            else:
                raise ValueError(f"Invalid selector key: {key}")

        return self._by, self._value
