"""
测试视频帧匹配功能的示例脚本

使用方法:
1. 准备一个模板图片和一个 MP4 视频文件
2. 运行脚本查看匹配结果
"""

from pathlib import Path

from hermes._media.video_calc import find_image_in_video
from hermes.models.media import MatchMethod


def test_basic_video_matching():
    """测试基本视频帧匹配"""

    template_path = Path("path/to/template.png")
    video_path = Path("path/to/video.mp4")

    # 基本匹配，每帧都检测
    results = find_image_in_video(
        template_path=template_path, video_path=video_path, threshold=0.8, skip_frames=1
    )

    print(f"\n找到 {len(results)} 个匹配帧:")
    for result in results:
        print(
            f"  时间: {result.timestamp:.2f}s, "
            f"置信度: {result.confidence:.3f}, "
            f"帧号: {result.frame_number}"
        )


def test_skip_frames():
    """测试跳帧策略"""

    template_path = Path("path/to/template.png")
    video_path = Path("path/to/video.mp4")

    # 每 5 帧检测一次，提高性能
    results = find_image_in_video(
        template_path=template_path, video_path=video_path, threshold=0.8, skip_frames=5
    )

    print(f"\n使用跳帧策略找到 {len(results)} 个匹配帧")


def test_specific_method():
    """测试使用特定匹配方法"""

    template_path = Path("path/to/template.png")
    video_path = Path("path/to/video.mp4")

    # 只使用标准模板匹配
    results = find_image_in_video(
        template_path=template_path,
        video_path=video_path,
        threshold=0.9,
        skip_frames=3,
        methods=[MatchMethod.TEMPLATE],
    )

    print(f"\n使用标准模板匹配找到 {len(results)} 个匹配帧")


def test_high_threshold():
    """测试高阈值匹配"""

    template_path = Path("path/to/template.png")
    video_path = Path("path/to/video.mp4")

    # 使用高阈值，只保留高置信度的匹配
    results = find_image_in_video(
        template_path=template_path,
        video_path=video_path,
        threshold=0.95,
        skip_frames=2,
    )

    print(f"\n高阈值匹配找到 {len(results)} 个匹配帧")


if __name__ == "__main__":
    print("=" * 60)
    print("视频帧匹配功能测试")
    print("=" * 60)

    # 取消注释以运行相应的测试
    # test_basic_video_matching()
    # test_skip_frames()
    # test_specific_method()
    # test_high_threshold()

    print("\n请修改图片和视频路径后运行测试")
