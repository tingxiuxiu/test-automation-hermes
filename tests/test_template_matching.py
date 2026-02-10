"""
测试模板匹配功能的示例脚本

使用方法:
1. 准备资源图片 (大图) 和模板图片 (小图)
2. 运行脚本查看匹配结果
"""

from pathlib import Path

from hermes._media.image_calc import MatchMethod, find_all_templates


def test_template_matching():
    """测试模板匹配功能"""

    # 示例：查找所有匹配的模板
    # 请替换为实际的图片路径
    resource_path = Path("path/to/resource_image.png")  # 资源图片（大图）
    template_path = Path("path/to/template_image.png")  # 模板图片（小图）

    # 使用所有匹配方法，阈值设为 0.8
    results = find_all_templates(
        resource_path=resource_path,
        template_path=template_path,
        threshold=0.8,
        methods=None,  # 使用所有方法：TEMPLATE, MULTI_SCALE, FEATURE
    )

    print(f"找到 {len(results)} 个匹配结果:")
    for i, result in enumerate(results, 1):
        print(f"\n匹配 {i}:")
        print(f"  置信度: {result.confidence:.3f}")
        print(
            f"  位置: left={result.bounds.left}, top={result.bounds.top}, "
            f"right={result.bounds.right}, bottom={result.bounds.bottom}"
        )
        print(f"  方法: {result.method}")


def test_specific_method():
    """测试特定匹配方法"""

    resource_path = Path("path/to/resource_image.png")
    template_path = Path("path/to/template_image.png")

    # 只使用标准模板匹配
    results = find_all_templates(
        resource_path=resource_path,
        template_path=template_path,
        threshold=0.85,
        methods=[MatchMethod.TEMPLATE],  # 只使用标准模板匹配
    )

    print(f"使用标准模板匹配找到 {len(results)} 个结果")


def test_multi_scale():
    """测试多尺度匹配"""

    resource_path = Path("path/to/resource_image.png")
    template_path = Path("path/to/template_image.png")

    # 使用多尺度匹配，适合模板和目标尺寸不完全一致的情况
    results = find_all_templates(
        resource_path=resource_path,
        template_path=template_path,
        threshold=0.75,
        methods=[MatchMethod.MULTI_SCALE],
    )

    print(f"使用多尺度匹配找到 {len(results)} 个结果")


def test_feature_matching():
    """测试特征匹配"""

    resource_path = Path("path/to/resource_image.png")
    template_path = Path("path/to/template_image.png")

    # 使用特征匹配，适合有旋转或变形的情况
    results = find_all_templates(
        resource_path=resource_path,
        template_path=template_path,
        threshold=0.3,  # 特征匹配的阈值表示最小匹配点数比例
        methods=[MatchMethod.FEATURE],
    )

    print(f"使用特征匹配找到 {len(results)} 个结果")


if __name__ == "__main__":
    # 运行测试
    print("=" * 60)
    print("模板匹配功能测试")
    print("=" * 60)

    # 取消注释以运行相应的测试
    # test_template_matching()
    # test_specific_method()
    # test_multi_scale()
    # test_feature_matching()

    print("\n请修改图片路径后运行测试")
