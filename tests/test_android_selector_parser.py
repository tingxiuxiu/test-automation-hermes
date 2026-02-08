from hermes._android.selector_paser import SelectorParser
from hermes.models.language import Language
from hermes.models.selector import (
    Selector,
    SelectorKey,
    Method,
    ImageSelector,
    MultiLanguageImageSelector,
    MultiLanguageSelector,
)
from pathlib import Path


class TestSelectorParser:
    def test_default_combination(self):
        """测试默认组合（无combination参数）情况下的选择器解析"""
        selector = Selector(id="com.example:id/button")
        parser = SelectorParser(selector, Language.ENGLISH)
        assert parser.get_method() == Method.XPATH
        assert parser.get_xpath() == '//*[@resource-id="com.example:id/button"]'

    def test_default_combination_with_multi_language(self):
        """测试默认组合（无combination参数）情况下的多语言选择器解析"""
        selector = Selector(
            id=MultiLanguageSelector(
                english="com.example:id/button", chinese="com.example:id/button_zh"
            )
        )
        parser = SelectorParser(selector, Language.CHINESE)
        assert parser.get_method() == Method.XPATH
        assert parser.get_xpath() == '//*[@resource-id="com.example:id/button_zh"]'

    def test_specified_combination(self):
        """测试指定combination情况下的选择器解析"""
        selector = Selector(id="com.example:id/button", text="Click Me")
        parser = SelectorParser(
            selector, Language.ENGLISH, combination=[SelectorKey.ID, SelectorKey.TEXT]
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//*[@resource-id="com.example:id/button" and @text="Click Me"]'
        )

    def test_specified_combination_with_multi_language(self):
        """测试指定combination情况下的多语言选择器解析"""
        selector = Selector(
            id=MultiLanguageSelector(
                english="com.example:id/button", chinese="com.example:id/button_zh"
            ),
            text=MultiLanguageSelector(english="Click Me", chinese="点击我"),
        )
        parser = SelectorParser(
            selector, Language.CHINESE, combination=[SelectorKey.ID, SelectorKey.TEXT]
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//*[@resource-id="com.example:id/button_zh" and @text="点击我"]'
        )

    def test_xpath_selector(self):
        """测试XPATH选择器的解析"""
        selector = Selector(xpath="//android.widget.Button[@text='Click Me']")
        parser = SelectorParser(selector, Language.ENGLISH)
        assert parser.get_method() == Method.XPATH
        assert parser.get_xpath() == "//android.widget.Button[@text='Click Me']"

    def test_multi_language_xpath_selector(self):
        """测试多语言XPATH选择器的解析"""
        selector = Selector(
            xpath=MultiLanguageSelector(
                english="//android.widget.Button[@text='Click Me']",
                chinese="//android.widget.Button[@text='点击我']",
            )
        )
        parser = SelectorParser(selector, Language.CHINESE)
        assert parser.get_method() == Method.XPATH
        assert parser.get_xpath() == "//android.widget.Button[@text='点击我']"

    def test_image_selector(self):
        """测试IMAGE选择器的解析"""
        selector = Selector(image=ImageSelector(path=Path("test.png"), threshold=0.9))
        parser = SelectorParser(selector, Language.ENGLISH)
        assert parser.get_method() == Method.IMAGE
        assert parser.get_image() == Path("test.png")
        assert parser.get_threshold() == 0.9

    def test_multi_language_image_selector(self):
        """测试多语言IMAGE选择器的解析"""
        selector = Selector(
            image=MultiLanguageImageSelector(
                english=ImageSelector(path=Path("test.png"), threshold=0.9),
                chinese=ImageSelector(path=Path("test_zh.png"), threshold=0.9),
            )
        )
        parser = SelectorParser(selector, Language.CHINESE)
        assert parser.get_method() == Method.IMAGE
        assert parser.get_image() == Path("test_zh.png")
        assert parser.get_threshold() == 0.9

    def test_class_name_selector(self):
        """测试CLASS_NAME选择器的解析"""
        selector = Selector(class_name="android.widget.Button")
        parser = SelectorParser(selector, Language.ENGLISH)
        assert parser.get_method() == Method.XPATH
        assert parser.get_xpath() == "//android.widget.Button"

    def test_multi_language_class_name_selector(self):
        """测试多语言CLASS_NAME选择器的解析"""
        selector = Selector(
            class_name=MultiLanguageSelector(
                english="android.widget.Button", chinese="android.widget.Button_zh"
            )
        )
        parser = SelectorParser(selector, Language.CHINESE)
        assert parser.get_method() == Method.XPATH
        assert parser.get_xpath() == "//android.widget.Button_zh"

    def test_text_selectors(self):
        """测试文本相关选择器的解析（TEXT、TEXT_STARTS_WITH等）"""
        # 测试TEXT选择器
        selector_text = Selector(text="Click Me")
        parser_text = SelectorParser(selector_text, Language.ENGLISH)
        assert parser_text.get_xpath() == '//*[@text="Click Me"]'

        # 测试TEXT_STARTS_WITH选择器
        selector_starts_with = Selector(text_starts_with="Click")
        parser_starts_with = SelectorParser(selector_starts_with, Language.ENGLISH)
        assert parser_starts_with.get_xpath() == '//*[starts-with(@text, "Click")]'

        # 测试TEXT_ENDS_WITH选择器
        selector_ends_with = Selector(text_ends_with="Me")
        parser_ends_with = SelectorParser(selector_ends_with, Language.ENGLISH)
        assert parser_ends_with.get_xpath() == '//*[ends-with(@text, "Me")]'

        # 测试TEXT_CONTAINS选择器
        selector_contains = Selector(text_contains="ick M")
        parser_contains = SelectorParser(selector_contains, Language.ENGLISH)
        assert parser_contains.get_xpath() == '//*[contains(@text, "ick M")]'

        # 测试TEXT_MATCHES选择器
        selector_matches = Selector(text_matches=".*Click.*")
        parser_matches = SelectorParser(selector_matches, Language.ENGLISH)
        assert parser_matches.get_xpath() == '//*[matches(@text, ".*Click.*")]'

    def test_multi_language_text_selector(self):
        """测试多语言TEXT选择器的解析"""
        selector = Selector(
            text=MultiLanguageSelector(english="Click Me", chinese="点击我")
        )
        parser = SelectorParser(selector, Language.CHINESE)
        assert parser.get_xpath() == '//*[@text="点击我"]'

        # 测试TEXT START 多语言选择器
        selector_starts_with = Selector(
            text_starts_with=MultiLanguageSelector(english="Click", chinese="点击")
        )
        parser_starts_with = SelectorParser(selector_starts_with, Language.CHINESE)
        assert parser_starts_with.get_xpath() == '//*[starts-with(@text, "点击")]'

        # 测试TEXT ENDS WITH 多语言选择器
        selector_ends_with = Selector(
            text_ends_with=MultiLanguageSelector(english="Me", chinese="我")
        )
        parser_ends_with = SelectorParser(selector_ends_with, Language.CHINESE)
        assert parser_ends_with.get_xpath() == '//*[ends-with(@text, "我")]'

        # 测试TEXT CONTAINS 多语言选择器
        selector_contains = Selector(
            text_contains=MultiLanguageSelector(english="ick M", chinese="ick 我")
        )
        parser_contains = SelectorParser(selector_contains, Language.CHINESE)
        assert parser_contains.get_xpath() == '//*[contains(@text, "ick 我")]'

        # 测试TEXT MATCHES 多语言选择器
        selector_matches = Selector(
            text_matches=MultiLanguageSelector(english=".*Click.*", chinese=".*点击.*")
        )
        parser_matches = SelectorParser(selector_matches, Language.CHINESE)
        assert parser_matches.get_xpath() == '//*[matches(@text, ".*点击.*")]'

    def test_description_selectors(self):
        """测试描述相关选择器的解析（DESCRIPTION、DESCRIPTION_STARTS_WITH等）"""
        # 测试DESCRIPTION选择器
        selector_desc = Selector(description="Submit button")
        parser_desc = SelectorParser(selector_desc, Language.ENGLISH)
        assert parser_desc.get_xpath() == '//*[@content-desc="Submit button"]'

        # 测试DESCRIPTION_STARTS_WITH选择器
        selector_starts_with = Selector(description_starts_with="Submit")
        parser_starts_with = SelectorParser(selector_starts_with, Language.ENGLISH)
        assert (
            parser_starts_with.get_xpath()
            == '//*[starts-with(@content-desc, "Submit")]'
        )

        # 测试DESCRIPTION_ENDS_WITH选择器
        selector_ends_with = Selector(description_ends_with="button")
        parser_ends_with = SelectorParser(selector_ends_with, Language.ENGLISH)
        assert parser_ends_with.get_xpath() == '//*[ends-with(@content-desc, "button")]'

        # 测试DESCRIPTION_CONTAINS选择器
        selector_contains = Selector(description_contains="mit bu")
        parser_contains = SelectorParser(selector_contains, Language.ENGLISH)
        assert parser_contains.get_xpath() == '//*[contains(@content-desc, "mit bu")]'

        # 测试DESCRIPTION_MATCHES选择器
        selector_matches = Selector(description_matches=".*Submit.*")
        parser_matches = SelectorParser(selector_matches, Language.ENGLISH)
        assert parser_matches.get_xpath() == '//*[matches(@content-desc, ".*Submit.*")]'

    def test_multi_language_description_selector(self):
        """测试多语言DESCRIPTION选择器的解析"""
        selector = Selector(
            description=MultiLanguageSelector(
                english="Submit button", chinese="提交按钮"
            )
        )
        parser = SelectorParser(selector, Language.CHINESE)
        assert parser.get_xpath() == '//*[@content-desc="提交按钮"]'

        # 测试DESCRIPTION_STARTS_WITH 多语言选择器
        selector_starts_with = Selector(
            description_starts_with=MultiLanguageSelector(
                english="Submit", chinese="提交"
            )
        )
        parser_starts_with = SelectorParser(selector_starts_with, Language.CHINESE)
        assert (
            parser_starts_with.get_xpath() == '//*[starts-with(@content-desc, "提交")]'
        )

        # 测试DESCRIPTION_ENDS_WITH 多语言选择器
        selector_ends_with = Selector(
            description_ends_with=MultiLanguageSelector(
                english="button", chinese="按钮"
            )
        )
        parser_ends_with = SelectorParser(selector_ends_with, Language.CHINESE)
        assert parser_ends_with.get_xpath() == '//*[ends-with(@content-desc, "按钮")]'

        # 测试DESCRIPTION_CONTAINS 多语言选择器
        selector_contains = Selector(
            description_contains=MultiLanguageSelector(
                english="mit bu", chinese="mit 按钮"
            )
        )
        parser_contains = SelectorParser(selector_contains, Language.CHINESE)
        assert parser_contains.get_xpath() == '//*[contains(@content-desc, "mit 按钮")]'

        # 测试DESCRIPTION_MATCHES 多语言选择器
        selector_matches = Selector(
            description_matches=MultiLanguageSelector(
                english=".*Submit.*", chinese=".*提交.*"
            )
        )
        parser_matches = SelectorParser(selector_matches, Language.CHINESE)
        assert parser_matches.get_xpath() == '//*[matches(@content-desc, ".*提交.*")]'

    def test_edge_cases(self):
        """测试边界情况和异常处理"""
        # 测试无效的选择器（无有效选择器）
        selector = Selector()
        try:
            parser = SelectorParser(selector, Language.ENGLISH)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No valid selector found" in str(e)

        # 测试无效的选择器键
        selector = Selector(id="com.example:id/button")
        try:
            parser = SelectorParser(
                selector, Language.ENGLISH, combination=["INVALID_KEY"]
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid selector key" in str(e)

        # 测试在组合中使用IMAGE选择器
        selector = Selector(id="com.example:id/button")
        try:
            parser = SelectorParser(
                selector,
                Language.ENGLISH,
                combination=[SelectorKey.ID, SelectorKey.IMAGE],
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Image selector is not supported in combination" in str(e)

        # 测试在组合中使用XPATH选择器
        selector = Selector(id="com.example:id/button")
        try:
            parser = SelectorParser(
                selector,
                Language.ENGLISH,
                combination=[SelectorKey.ID, SelectorKey.XPATH],
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Xpath selector is not supported in combination" in str(e)

    def test_combined_selectors(self):
        """测试组合选择器的解析"""
        selector = Selector(
            id="com.example:id/button",
            text="Click Me",
            class_name="android.widget.Button",
        )
        parser = SelectorParser(
            selector,
            Language.ENGLISH,
            combination=[SelectorKey.CLASS_NAME, SelectorKey.ID, SelectorKey.TEXT],
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//android.widget.Button[@resource-id="com.example:id/button" and @text="Click Me"]'
        )

    def test_combined_selectors_with_description(self):
        """测试组合选择器与DESCRIPTION选择器的解析"""
        selector = Selector(
            id="com.example:id/button",
            description="Submit button",
            class_name="android.widget.Button",
        )
        parser = SelectorParser(
            selector,
            Language.ENGLISH,
            combination=[
                SelectorKey.CLASS_NAME,
                SelectorKey.ID,
                SelectorKey.DESCRIPTION,
            ],
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//android.widget.Button[@resource-id="com.example:id/button" and @content-desc="Submit button"]'
        )

    def test_combined_selectors_with_description_ends_with(self):
        """测试组合选择器与DESCRIPTION_ENDS_WITH选择器的解析"""
        selector = Selector(
            id="com.example:id/button",
            description_ends_with=MultiLanguageSelector(
                english="button", chinese="按钮"
            ),
            class_name="android.widget.Button",
        )
        parser = SelectorParser(
            selector,
            Language.CHINESE,
            combination=[
                SelectorKey.CLASS_NAME,
                SelectorKey.ID,
                SelectorKey.DESCRIPTION_ENDS_WITH,
            ],
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//android.widget.Button[@resource-id="com.example:id/button" and ends-with(@content-desc, "按钮")]'
        )

    def test_combined_selectors_with_description_starts_with(self):
        """测试组合选择器与DESCRIPTION_STARTS_WITH选择器的解析"""
        selector = Selector(
            id="com.example:id/button",
            description_starts_with=MultiLanguageSelector(
                english="Submit", chinese="提交"
            ),
            class_name="android.widget.Button",
        )
        parser = SelectorParser(
            selector,
            Language.CHINESE,
            combination=[
                SelectorKey.CLASS_NAME,
                SelectorKey.ID,
                SelectorKey.DESCRIPTION_STARTS_WITH,
            ],
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//android.widget.Button[@resource-id="com.example:id/button" and starts-with(@content-desc, "提交")]'
        )

    def test_combined_selectors_with_description_contains(self):
        """测试组合选择器与DESCRIPTION_CONTAINS选择器的解析"""
        selector = Selector(
            id="com.example:id/button",
            description_contains=MultiLanguageSelector(
                english="Submit", chinese="提交"
            ),
            class_name="android.widget.Button",
        )
        parser = SelectorParser(
            selector,
            Language.CHINESE,
            combination=[
                SelectorKey.CLASS_NAME,
                SelectorKey.ID,
                SelectorKey.DESCRIPTION_CONTAINS,
            ],
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//android.widget.Button[@resource-id="com.example:id/button" and contains(@content-desc, "提交")]'
        )

    def test_combined_selectors_with_multiple_language(self):
        """测试组合选择器与多语言选择器的解析"""
        selector = Selector(
            id="com.example:id/button",
            description=MultiLanguageSelector(
                english="Submit button", chinese="提交按钮"
            ),
            class_name="android.widget.Button",
        )
        parser = SelectorParser(
            selector,
            Language.CHINESE,
            combination=[
                SelectorKey.CLASS_NAME,
                SelectorKey.ID,
                SelectorKey.DESCRIPTION,
            ],
        )
        assert parser.get_method() == Method.XPATH
        assert (
            parser.get_xpath()
            == '//android.widget.Button[@resource-id="com.example:id/button" and @content-desc="提交按钮"]'
        )

    def test_get_window(self):
        """测试get_window方法"""
        selector = Selector(id="com.example:id/button")
        parser = SelectorParser(selector, Language.ENGLISH)
        window = parser.get_window()
        assert window.name == "default"
        assert window.display_id == 0

    def test_invalid_xpath_getter(self):
        """测试无效的xpath getter"""
        selector = Selector(image={"path": Path("test.png")})
        parser = SelectorParser(selector, Language.ENGLISH)
        try:
            parser.get_xpath()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid xpath selector" in str(e)

    def test_invalid_image_getter(self):
        """测试无效的image getter"""
        selector = Selector(id="com.example:id/button")
        parser = SelectorParser(selector, Language.ENGLISH)
        try:
            parser.get_image()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid image selector" in str(e)
