<div align="center">

# 🚀 Hermes

**现代化跨平台 UI 自动化测试框架**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://github.com/astral-sh/ruff)

*简洁 · 高效 · 跨平台*

[English](#english) | [中文文档](#中文文档)

</div>

---

## English

### ✨ Features

- 🔥 **Simple API** - Intuitive and pythonic API design
- 🌍 **Multi-Language Support** - Built-in i18n for selectors (Chinese, English, Japanese, Korean, etc.)
- 📱 **Cross-Platform** - Support Android, iOS, and HarmonyOS
- 🎯 **Multiple Locator Strategies** - XPath, JSONPath, Image Recognition
- 🖼️ **Image Recognition** - Template matching with multi-scale and feature-based algorithms
- 📊 **Rich Reporting** - Built-in step tracking and reporting
- 🔌 **Plugin System** - Extensible plugin architecture
- ⚡ **High Performance** - Page caching and optimized element location

### 📦 Installation

```bash
pip install test-automation-hermes
```

### 🚀 Quick Start

```python
from hermes import new_device, step
from hermes.models.device import AndroidDeviceModel
from hermes.models.selector import Selector
from hermes.models.language import Language

# Create device connection
device = new_device(AndroidDeviceModel(
    serial="emulator-5554",
    language=Language.ENGLISH
))

# Connect to device
device.connect()

# Locate element by text
selector = Selector(text="Login")
element = device.driver.locator(selector)

# Tap element
device.driver.tap(selector)

# Swipe gesture
from hermes.models.component import Point
device.driver.swipe(
    Point(x=500, y=1500),
    Point(x=500, y=500)
)

# Disconnect
device.disconnect()
```

### 📖 Selector Examples

```python
from hermes.models.selector import Selector

# Text selector
selector = Selector(text="Hello World")

# ID selector
selector = Selector(id="com.example:id/button")

# XPath selector
selector = Selector(xpath="//android.widget.Button[@text='Login']")

# JSONPath selector
selector = Selector(jsonpath='$[?(@.text == "Login")]')

# Class name selector
selector = Selector(class_name="android.widget.Button")

# Text contains selector
selector = Selector(text_contains="Hello")

# Text starts with selector
selector = Selector(text_starts_with="Hello")

# Text matches (regex) selector
selector = Selector(text_matches="^Hello.*World$")

# Image selector
from hermes.models.selector import ImageSelector
from pathlib import Path
selector = Selector(image=ImageSelector(
    path=Path("button.png"),
    threshold=0.9
))

# Multi-language selector
from hermes.models.selector import MultiLanguageSelector
selector = Selector(text=MultiLanguageSelector(
    english="Settings",
    chinese="设置",
    japanese="設定"
))
```

### 🎯 Step Tracking

```python
from hermes import step

# Use as decorator
@step("Login with username: {username}")
def login(username: str, password: str):
    device.driver.tap(Selector(text=username))
    # ...

# Use as context manager
with step("Perform login"):
    device.driver.tap(Selector(text="Login"))
```

### 🖼️ Image Recognition

```python
from hermes._media.image_calculate import find_all_templates, compare_similarity
from hermes.models.media import SimilarityAlgorithm
from pathlib import Path

# Find all template matches
results = find_all_templates(
    resource_path=Path("screenshot.png"),
    template_path=Path("button.png"),
    threshold=0.85
)

for result in results:
    print(f"Found at {result.bounds} with confidence {result.confidence}")

# Compare image similarity
score = compare_similarity(
    Path("image1.png"),
    Path("image2.png"),
    algorithm=SimilarityAlgorithm.SSIM
)
```

### 📁 Project Structure

```
hermes/
├── _android/          # Android platform implementation
│   ├── android_adb.py
│   ├── android_device.py
│   ├── android_driver.py
│   ├── android_component.py
│   ├── selector_to_xpath.py
│   └── selector_to_jsonpath.py
├── _core/             # Core functionality
│   ├── config.py
│   ├── context.py
│   ├── step.py
│   └── hermes_cache.py
├── _media/            # Media processing
│   ├── image_calculate.py
│   └── image_component.py
├── models/            # Data models
│   ├── selector.py
│   ├── device.py
│   ├── component.py
│   └── language.py
├── protocol/          # Protocol definitions
│   ├── driver_protocol.py
│   ├── component_protocol.py
│   └── debug_bridge_protocol.py
└── utils/             # Utilities
```

---

## 中文文档

### ✨ 特性

- 🔥 **简洁 API** - 直观且符合 Python 风格的 API 设计
- 🌍 **多语言支持** - 内置选择器国际化支持（中文、英文、日文、韩文等）
- 📱 **跨平台** - 支持 Android、iOS 和鸿蒙系统
- 🎯 **多种定位策略** - 支持 XPath、JSONPath、图像识别
- 🖼️ **图像识别** - 支持多尺度和基于特征的模板匹配算法
- 📊 **丰富报告** - 内置步骤追踪和报告生成
- 🔌 **插件系统** - 可扩展的插件架构
- ⚡ **高性能** - 页面缓存和优化的元素定位

### 📦 安装

```bash
pip install test-automation-hermes
```

### 🚀 快速开始

```python
from hermes import new_device, step
from hermes.models.device import AndroidDeviceModel
from hermes.models.selector import Selector
from hermes.models.language import Language

# 创建设备连接
device = new_device(AndroidDeviceModel(
    serial="emulator-5554",
    language=Language.CHINESE
))

# 连接设备
device.connect()

# 通过文本定位元素
selector = Selector(text="登录")
element = device.driver.locator(selector)

# 点击元素
device.driver.tap(selector)

# 滑动手势
from hermes.models.component import Point
device.driver.swipe(
    Point(x=500, y=1500),
    Point(x=500, y=500)
)

# 断开连接
device.disconnect()
```

### 📖 选择器示例

```python
from hermes.models.selector import Selector

# 文本选择器
selector = Selector(text="你好世界")

# ID 选择器
selector = Selector(id="com.example:id/button")

# XPath 选择器
selector = Selector(xpath="//android.widget.Button[@text='登录']")

# JSONPath 选择器
selector = Selector(jsonpath='$[?(@.text == "登录")]')

# 类名选择器
selector = Selector(class_name="android.widget.Button")

# 文本包含选择器
selector = Selector(text_contains="你好")

# 文本开头匹配选择器
selector = Selector(text_starts_with="你好")

# 文本正则匹配选择器
selector = Selector(text_matches="^你好.*世界$")

# 图像选择器
from hermes.models.selector import ImageSelector
from pathlib import Path
selector = Selector(image=ImageSelector(
    path=Path("button.png"),
    threshold=0.9
))

# 多语言选择器
from hermes.models.selector import MultiLanguageSelector
selector = Selector(text=MultiLanguageSelector(
    english="Settings",
    chinese="设置",
    japanese="設定"
))
```

### 🎯 步骤追踪

```python
from hermes import step

# 作为装饰器使用
@step("使用用户名登录: {username}")
def login(username: str, password: str):
    device.driver.tap(Selector(text=username))
    # ...

# 作为上下文管理器使用
with step("执行登录操作"):
    device.driver.tap(Selector(text="登录"))
```

### 🖼️ 图像识别

```python
from hermes._media.image_calculate import find_all_templates, compare_similarity
from hermes.models.media import SimilarityAlgorithm
from pathlib import Path

# 查找所有模板匹配
results = find_all_templates(
    resource_path=Path("screenshot.png"),
    template_path=Path("button.png"),
    threshold=0.85
)

for result in results:
    print(f"在 {result.bounds} 找到匹配，置信度 {result.confidence}")

# 比较图像相似度
score = compare_similarity(
    Path("image1.png"),
    Path("image2.png"),
    algorithm=SimilarityAlgorithm.SSIM
)
```

### 🔧 支持的定位引擎

| 引擎 | 描述 | 示例 |
|------|------|------|
| XPath | XML 路径语言 | `Selector(xpath="//Button[@text='Login']")` |
| JSONPath | JSON 路径查询 | `Selector(jsonpath='$[?(@.text=="Login")]')` |
| Image | 图像模板匹配 | `Selector(image=ImageSelector(path="btn.png"))` |

### 🌍 支持的语言

| 语言 | 代码 |
|------|------|
| 简体中文 | `Language.CHINESE` |
| 繁体中文 | `Language.CHINESE_TRADITIONAL` |
| 英语 | `Language.ENGLISH` |
| 日语 | `Language.JAPANESE` |
| 韩语 | `Language.KOREAN` |
| 德语 | `Language.GERMAN` |
| 法语 | `Language.FRENCH` |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

- Author: xin.zhang
- Email: 112859811@qq.com

---

<div align="center">

**⭐ If this project helps you, please give it a star! ⭐**

Made with ❤️ by the Hermes Team

</div>
