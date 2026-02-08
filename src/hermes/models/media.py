from enum import Enum

from pydantic import BaseModel

from .component import Bounds, Point, Size


class MatchMethod(Enum):
    """模板匹配方法枚举"""

    TEMPLATE = "template"  # 标准模板匹配
    MULTI_SCALE = "multi_scale"  # 多尺度模板匹配
    FEATURE = "feature"  # 基于特征的匹配


class SimilarityAlgorithm(Enum):
    """图片相似度算法枚举"""

    HISTOGRAM = "histogram"  # 直方图比较
    SSIM = "ssim"  # 结构相似度
    ORB = "orb"  # ORB特征匹配
    PHASH = "phash"  # 感知哈希


class ImageModal(BaseModel):
    tag: str
    size: Size
    center: Point
    bounds: Bounds


class MatchResult(BaseModel):
    """模板匹配结果

    Attributes:
        confidence: 匹配置信度，范围 0-1，1 表示完全匹配
        bounds: 匹配区域的边界框 (left, top, right, bottom)
        method: 使用的匹配方法名称
    """

    confidence: float
    bounds: Bounds
    method: str


class VideoMatchResult(BaseModel):
    """视频帧匹配结果

    Attributes:
        timestamp: 帧的时间戳（秒）
        confidence: 匹配置信度，范围 0-1，1 表示完全匹配
        frame_number: 帧号（从 0 开始）
    """

    timestamp: float
    confidence: float
    frame_number: int
