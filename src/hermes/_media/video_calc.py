import tempfile
from collections.abc import Sequence
from pathlib import Path

import cv2

from ..models.media import MatchMethod, VideoMatchResult
from . import image_calc


def find_image_in_video(
    template_path: Path,
    video_path: Path,
    threshold: float = 0.8,
    skip_frames: int = 1,
    methods: Sequence[MatchMethod] | None = None,
) -> Sequence[VideoMatchResult]:
    """在视频中查找包含指定图片的所有帧

    该方法逐帧读取视频，使用模板匹配算法查找包含指定图片的帧。
    支持跳帧策略以提高性能。

    原理：
    1. 使用 OpenCV 打开视频文件
    2. 逐帧读取视频（可选跳帧）
    3. 对每一帧使用模板匹配算法
    4. 记录匹配成功的帧的时间戳和置信度
    5. 根据帧号和 FPS 计算精确时间戳

    性能优化：
    - skip_frames: 跳帧策略，例如 skip_frames=5 表示每 5 帧检测一次
    - 这可以显著提高处理速度，但可能会错过某些匹配

    Args:
        template_path: 模板图片路径
        video_path: 视频文件路径（MP4 等格式）
        threshold: 匹配置信度阈值，范围 0-1，默认 0.8
        skip_frames: 跳帧间隔，1 表示每帧都检测，5 表示每 5 帧检测一次
        methods: 要使用的匹配方法列表，默认使用所有方法

    Returns:
        匹配结果列表，每个结果包含时间戳、置信度和帧号

    Example:
        >>> results = find_image_in_video(
        ...     Path("button.png"),
        ...     Path("video.mp4"),
        ...     threshold=0.85,
        ...     skip_frames=5
        ... )
        >>> for result in results:
        ...     print(f"时间: {result.timestamp:.2f}s, "
        ...           f"置信度: {result.confidence:.3f}, "
        ...           f"帧号: {result.frame_number}")

        # 只使用标准模板匹配
        >>> results = find_image_in_video(
        ...     Path("button.png"),
        ...     Path("video.mp4"),
        ...     threshold=0.9,
        ...     methods=[MatchMethod.TEMPLATE]
        ... )
    """
    # 打开视频文件
    video = cv2.VideoCapture(str(video_path))

    if not video.isOpened():
        print(f"警告: 无法打开视频文件 {video_path}")
        return []

    try:
        # 获取视频信息
        fps = video.get(cv2.CAP_PROP_FPS)  # 帧率
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))  # 总帧数

        print(f"视频信息: FPS={fps:.2f}, 总帧数={total_frames}")

        # 存储匹配结果
        matches = []

        # 当前帧号
        frame_number = 0

        # 创建临时目录存储帧图片
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            while True:
                # 读取一帧
                ret, frame = video.read()

                # 如果读取失败，说明视频结束
                if not ret:
                    break

                # 跳帧策略：只处理指定间隔的帧
                if frame_number % skip_frames == 0:
                    # 保存当前帧为临时图片
                    frame_path = temp_dir_path / f"frame_{frame_number}.jpg"
                    cv2.imwrite(str(frame_path), frame)

                    # 使用模板匹配查找图片
                    match_results = image_calc.find_all_templates(
                        resource_path=frame_path,
                        template_path=template_path,
                        threshold=threshold,
                        methods=methods,
                    )

                    # 如果找到匹配，记录结果
                    if match_results:
                        # 取置信度最高的匹配
                        best_match = max(match_results, key=lambda x: x.confidence)

                        # 计算时间戳（秒）
                        timestamp = frame_number / fps if fps > 0 else 0

                        # 创建视频匹配结果
                        video_match = VideoMatchResult(
                            timestamp=timestamp,
                            confidence=best_match.confidence,
                            frame_number=frame_number,
                        )

                        matches.append(video_match)

                        print(
                            f"找到匹配: 帧号={frame_number}, "
                            f"时间={timestamp:.2f}s, "
                            f"置信度={best_match.confidence:.3f}"
                        )

                    # 删除临时帧图片以节省空间
                    frame_path.unlink(missing_ok=True)

                frame_number += 1

                # 显示进度（每 100 帧）
                if frame_number % 100 == 0:
                    progress = (
                        (frame_number / total_frames) * 100 if total_frames > 0 else 0
                    )
                    print(f"处理进度: {frame_number}/{total_frames} ({progress:.1f}%)")

        print(f"处理完成: 共 {frame_number} 帧，找到 {len(matches)} 个匹配")

        return matches

    finally:
        # 释放视频资源
        video.release()
