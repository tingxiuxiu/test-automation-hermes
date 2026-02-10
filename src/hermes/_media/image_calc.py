from collections.abc import Sequence
from pathlib import Path

import cv2
import numpy as np

from ..models.component import Bounds
from ..models.media import MatchMethod, MatchResult, SimilarityAlgorithm


def find_all_templates(
    resource_path: Path,
    template_path: Path,
    threshold: float = 0.8,
    methods: Sequence[MatchMethod] | None = None,
) -> Sequence[MatchResult]:
    """在资源图片中查找所有模板图片的匹配位置

    该方法使用多种算法在资源图片中查找模板图片的所有出现位置。
    支持标准模板匹配、多尺度匹配和基于特征的匹配。

    Args:
        resource_path: 资源图片路径（大图）
        template_path: 模板图片路径（小图）
        threshold: 匹配置信度阈值，范围 0-1，默认 0.8
        methods: 要使用的匹配方法列表，默认使用所有方法

    Returns:
        匹配结果列表，每个结果包含置信度、边界框和匹配方法

    Example:
        >>> results = find_all_templates(
        ...     Path("screenshot.png"),
        ...     Path("button.png"),
        ...     threshold=0.85
        ... )
        >>> for result in results:
        ...     print(f"Found at {result.bounds} with confidence {result.confidence}")

        # 只使用标准模板匹配
        >>> results = find_all_templates(
        ...     Path("screenshot.png"),
        ...     Path("button.png"),
        ...     threshold=0.85,
        ...     methods=[MatchMethod.TEMPLATE]
        ... )
        # 只使用多尺度匹配
        >>> results = find_all_templates(
        ...     Path("screenshot.png"),
        ...     Path("button.png"),
        ...     threshold=0.75,
        ...     methods=[MatchMethod.MULTI_SCALE]
        ... )
        # 只使用特征匹配（适合旋转场景）
        >>> results = find_all_templates(
        ...     Path("screenshot.png"),
        ...     Path("button.png"),
        ...     threshold=0.3,  # 特征匹配的阈值表示最小匹配点数比例
        ...     methods=[MatchMethod.FEATURE]
        ... )
    """
    # 默认使用所有匹配方法
    if methods is None:
        methods = [
            MatchMethod.TEMPLATE,
            MatchMethod.MULTI_SCALE,
            MatchMethod.FEATURE,
        ]

    # 加载图片
    resource_img = _load_image(resource_path)
    template_img = _load_image(template_path)

    if resource_img is None or template_img is None:
        return []

    all_matches = []

    # 使用不同的匹配方法
    if MatchMethod.TEMPLATE in methods:
        matches = _template_matching(resource_img, template_img, threshold)
        all_matches.extend(matches)

    if MatchMethod.MULTI_SCALE in methods:
        matches = _multi_scale_matching(resource_img, template_img, threshold)
        all_matches.extend(matches)

    if MatchMethod.FEATURE in methods:
        matches = _feature_matching(resource_img, template_img, threshold)
        all_matches.extend(matches)

    # 使用非极大值抑制去除重叠的检测框
    final_matches = _non_max_suppression(all_matches, overlap_threshold=0.3)

    return final_matches


def _load_image(path: Path) -> np.ndarray | None:
    """加载图片文件

    Args:
        path: 图片文件路径

    Returns:
        OpenCV 图片对象，如果加载失败返回 None
    """
    img = cv2.imread(str(path))
    if img is None:
        print(f"警告: 无法加载图片 {path}")
    return img


def _template_matching(
    resource_img: np.ndarray,
    template_img: np.ndarray,
    threshold: float,
) -> list[MatchResult]:
    """标准模板匹配

    使用 OpenCV 的模板匹配算法在资源图片中查找模板。
    该方法使用归一化相关系数匹配 (TM_CCOEFF_NORMED)，对光照变化有一定鲁棒性。

    原理：
        1. 滑动窗口：模板在资源图片上滑动，计算每个位置的相似度
        2. 归一化相关系数：计算模板和窗口区域的相关性，范围 -1 到 1
        3. 阈值过滤：只保留相似度大于阈值的位置

    Args:
        resource_img: 资源图片
        template_img: 模板图片
        threshold: 匹配阈值

    Returns:
        匹配结果列表
    """
    # 转换为灰度图，提高匹配速度
    resource_gray = cv2.cvtColor(resource_img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

    h, w = template_gray.shape

    # 使用归一化相关系数匹配方法
    # TM_CCOEFF_NORMED: 归一化相关系数，对光照变化鲁棒
    result = cv2.matchTemplate(resource_gray, template_gray, cv2.TM_CCOEFF_NORMED)

    # 查找所有大于阈值的匹配位置
    locations = np.where(result >= threshold)
    matches = []

    # 转换为 (x, y) 格式
    for pt in zip(*locations[::-1]):  # noqa
        confidence = float(result[pt[1], pt[0]])
        bounds = Bounds(
            left=int(pt[0]),
            top=int(pt[1]),
            right=int(pt[0] + w),
            bottom=int(pt[1] + h),
        )
        matches.append(
            MatchResult(
                confidence=confidence, bounds=bounds, method="template_matching"
            )
        )

    return matches


def _multi_scale_matching(
    resource_img: np.ndarray,
    template_img: np.ndarray,
    threshold: float,
) -> list[MatchResult]:
    """多尺度模板匹配

    在不同尺度下进行模板匹配，用于处理模板和资源图片尺寸不完全一致的情况。

    原理：
        1. 图像金字塔：对模板图片进行多尺度缩放（0.5x 到 2.0x）
        2. 逐尺度匹配：在每个尺度下执行标准模板匹配
        3. 坐标还原：将匹配坐标映射回原始图片尺寸

    适用场景：
        - 模板和目标尺寸略有差异
        - 需要检测不同大小的相同对象

    Args:
        resource_img: 资源图片
        template_img: 模板图片
        threshold: 匹配阈值

    Returns:
        匹配结果列表
    """
    resource_gray = cv2.cvtColor(resource_img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

    matches = []

    # 定义缩放范围：0.5x 到 2.0x，步长 0.1
    scales = np.linspace(0.5, 2.0, 16)

    for scale in scales:
        # 缩放模板图片
        scaled_template = cv2.resize(
            template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR
        )

        h, w = scaled_template.shape

        # 如果缩放后的模板大于资源图片，跳过
        if h > resource_gray.shape[0] or w > resource_gray.shape[1]:
            continue

        # 执行模板匹配
        result = cv2.matchTemplate(resource_gray, scaled_template, cv2.TM_CCOEFF_NORMED)

        # 查找匹配位置
        locations = np.where(result >= threshold)

        for pt in zip(*locations[::-1]):  # noqa
            confidence = float(result[pt[1], pt[0]])
            bounds = Bounds(
                left=int(pt[0]),
                top=int(pt[1]),
                right=int(pt[0] + w),
                bottom=int(pt[1] + h),
            )
            matches.append(
                MatchResult(
                    confidence=confidence,
                    bounds=bounds,
                    method=f"multi_scale_{scale:.2f}x",
                )
            )

    return matches


def _feature_matching(
    resource_img: np.ndarray,
    template_img: np.ndarray,
    threshold: float,
) -> list[MatchResult]:
    """基于特征的匹配

    使用 ORB (Oriented FAST and Rotated BRIEF) 特征检测和匹配。
    该方法对旋转、缩放和轻微变形具有鲁棒性。

    原理：
    1. 特征检测：使用 ORB 检测关键点和描述符
        - FAST: 快速角点检测
        - BRIEF: 二进制描述符，计算效率高
    2. 特征匹配：使用汉明距离匹配描述符
    3. 几何验证：使用 RANSAC 算法过滤误匹配
    4. 单应性变换：计算模板到资源图片的变换矩阵
    5. 边界框计算：通过变换矩阵计算匹配区域

    适用场景：
    - 模板有旋转
    - 模板有轻微变形
    - 视角有变化

    Args:
        resource_img: 资源图片
        template_img: 模板图片
        threshold: 匹配阈值（这里表示最小匹配点数比例）

    Returns:
        匹配结果列表
    """
    resource_gray = cv2.cvtColor(resource_img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

    # 创建 ORB 特征检测器
    # nfeatures: 最多检测的特征点数量
    orb = cv2.ORB_create(nfeatures=2000)

    # 检测关键点和计算描述符
    kp1, des1 = orb.detectAndCompute(template_gray, None)
    kp2, des2 = orb.detectAndCompute(resource_gray, None)

    if des1 is None or des2 is None or len(kp1) < 4:
        return []

    # 使用 BFMatcher 进行特征匹配
    # NORM_HAMMING: 汉明距离，适用于 ORB 的二进制描述符
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches_raw = bf.knnMatch(des1, des2, k=2)

    # Lowe's ratio test: 过滤不可靠的匹配
    # 如果最近邻距离 < 0.75 * 次近邻距离，则认为是好的匹配
    good_matches = []
    for match_pair in matches_raw:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

    # 需要至少 4 个匹配点才能计算单应性矩阵
    min_match_count = max(4, int(len(kp1) * threshold))

    if len(good_matches) < min_match_count:
        return []

    # 提取匹配点的坐标
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 使用 RANSAC 算法计算单应性矩阵
    # 单应性矩阵描述了模板到资源图片的投影变换
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    if M is None:
        return []

    # 计算内点（inliers）比例作为置信度
    inliers = np.sum(mask)
    confidence = float(inliers / len(good_matches))

    if confidence < threshold:
        return []

    # 计算模板在资源图片中的边界框
    h, w = template_gray.shape
    pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
    dst = cv2.perspectiveTransform(pts, M)

    # 提取边界框坐标
    x_coords = dst[:, 0, 0]
    y_coords = dst[:, 0, 1]

    bounds = Bounds(
        left=int(np.min(x_coords)),
        top=int(np.min(y_coords)),
        right=int(np.max(x_coords)),
        bottom=int(np.max(y_coords)),
    )

    return [
        MatchResult(confidence=confidence, bounds=bounds, method="feature_matching")
    ]


def _non_max_suppression(
    matches: list[MatchResult],
    overlap_threshold: float = 0.3,
) -> list[MatchResult]:
    """非极大值抑制 (Non-Maximum Suppression)

    去除重叠的检测框，只保留置信度最高的框。

    原理：
    1. 按置信度降序排序所有检测框
    2. 选择置信度最高的框，加入结果列表
    3. 计算该框与其他框的 IoU (Intersection over Union)
    4. 删除 IoU 大于阈值的框（认为是重复检测）
    5. 重复步骤 2-4，直到处理完所有框

    IoU 计算：
    IoU = 交集面积 / 并集面积

    Args:
        matches: 所有匹配结果
        overlap_threshold: IoU 阈值，超过该值认为是重叠

    Returns:
        去重后的匹配结果列表
    """
    if not matches:
        return []

    # 按置信度降序排序
    matches = sorted(matches, key=lambda x: x.confidence, reverse=True)

    keep = []

    while matches:
        # 选择置信度最高的框
        current = matches.pop(0)
        keep.append(current)

        # 过滤与当前框重叠度高的其他框
        filtered = []
        for match in matches:
            iou = _calculate_iou(current.bounds, match.bounds)
            if iou <= overlap_threshold:
                filtered.append(match)

        matches = filtered

    return keep


def _calculate_iou(bounds1: Bounds, bounds2: Bounds) -> float:
    """计算两个边界框的 IoU (Intersection over Union)

    IoU 是目标检测中常用的评估指标，表示两个框的重叠程度。

    计算公式：
    IoU = 交集面积 / 并集面积

    Args:
        bounds1: 第一个边界框
        bounds2: 第二个边界框

    Returns:
        IoU 值，范围 0-1
    """
    # 计算交集区域
    x_left = max(bounds1.left, bounds2.left)
    y_top = max(bounds1.top, bounds2.top)
    x_right = min(bounds1.right, bounds2.right)
    y_bottom = min(bounds1.bottom, bounds2.bottom)

    # 如果没有交集
    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # 计算交集面积
    intersection = (x_right - x_left) * (y_bottom - y_top)

    # 计算两个框的面积
    area1 = (bounds1.right - bounds1.left) * (bounds1.bottom - bounds1.top)
    area2 = (bounds2.right - bounds2.left) * (bounds2.bottom - bounds2.top)

    # 计算并集面积
    union = area1 + area2 - intersection

    # 避免除零
    if union == 0:
        return 0.0

    return intersection / union


# ============================================================================
# 图片相似度对比功能
# ============================================================================


def compare_similarity(
    image1_path: Path,
    image2_path: Path,
    algorithm: SimilarityAlgorithm = SimilarityAlgorithm.HISTOGRAM,
) -> float:
    """对比两张图片的相似度

    使用指定的算法计算两张图片的相似度分数。

    Args:
        image1_path: 第一张图片路径
        image2_path: 第二张图片路径
        algorithm: 使用的相似度算法，默认为直方图比较

    Returns:
        相似度分数，范围 0-1，1 表示完全相同

    Example:
        >>> score = compare_similarity(
        ...     Path("image1.png"),
        ...     Path("image2.png"),
        ...     algorithm=SimilarityAlgorithm.HISTOGRAM
        ... )
        >>> print(f"相似度: {score:.3f}")

        # 使用 SSIM 算法
        >>> score = compare_similarity(
        ...     Path("image1.png"),
        ...     Path("image2.png"),
        ...     algorithm=SimilarityAlgorithm.SSIM
        ... )

        # 使用 ORB 特征匹配
        >>> score = compare_similarity(
        ...     Path("image1.png"),
        ...     Path("image2.png"),
        ...     algorithm=SimilarityAlgorithm.ORB
        ... )

        # 使用感知哈希
        >>> score = compare_similarity(
        ...     Path("image1.png"),
        ...     Path("image2.png"),
        ...     algorithm=SimilarityAlgorithm.PHASH
        ... )
    """
    # 加载图片
    img1 = _load_image(image1_path)
    img2 = _load_image(image2_path)

    if img1 is None or img2 is None:
        return 0.0

    # 根据算法选择相应的比较方法
    if algorithm == SimilarityAlgorithm.HISTOGRAM:
        return _compare_histogram(img1, img2)
    elif algorithm == SimilarityAlgorithm.SSIM:
        return _compare_ssim(img1, img2)
    elif algorithm == SimilarityAlgorithm.ORB:
        return _compare_orb(img1, img2)
    elif algorithm == SimilarityAlgorithm.PHASH:
        return _compare_phash(img1, img2)
    else:
        return 0.0


def _compare_histogram(img1: np.ndarray, img2: np.ndarray) -> float:
    """直方图比较

    通过对比颜色分布来判断相似度。该方法速度快，适合颜色分布相似的图片。

    原理：
    1. 转换为 HSV 色彩空间（更接近人眼感知）
    2. 计算 H（色调）和 S（饱和度）通道的 2D 直方图
    3. 归一化直方图
    4. 使用相关系数法比较两个直方图

    优点：
    - 速度快
    - 对颜色分布相似的图片效果好

    适用场景：
    - 快速比较颜色相似的图片
    - 不关心图片内容的空间结构

    Args:
        img1: 第一张图片
        img2: 第二张图片

    Returns:
        相似度分数，范围 0-1
    """
    # 转换为 HSV 色彩空间
    # HSV 比 RGB 更接近人眼对颜色的感知
    hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

    # 计算 H 和 S 通道的 2D 直方图
    # H 通道范围: 0-180, S 通道范围: 0-256
    # bins: 每个通道的直方图柱数
    hist1 = cv2.calcHist([hsv1], [0, 1], None, [50, 60], [0, 180, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1], None, [50, 60], [0, 180, 0, 256])

    # 归一化直方图，使其总和为 1
    cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

    # 使用相关系数法比较直方图
    # HISTCMP_CORREL: 相关系数法，返回值范围 -1 到 1
    # 1 表示完全相同，-1 表示完全相反
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    # 将范围从 [-1, 1] 转换为 [0, 1]
    return (similarity + 1) / 2


def _compare_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """结构相似度 (SSIM - Structural Similarity Index)

    考虑亮度、对比度和结构三个方面来评估图像相似度。
    该方法更接近人眼感知，适合评估图像质量。

    原理：
    SSIM 公式：SSIM(x,y) = [l(x,y)]^α · [c(x,y)]^β · [s(x,y)]^γ
    其中：
    - l(x,y): 亮度比较
    - c(x,y): 对比度比较
    - s(x,y): 结构比较
    通常 α = β = γ = 1

    简化公式：
    SSIM = (2μxμy + C1)(2σxy + C2) / ((μx² + μy² + C1)(σx² + σy² + C2))
    其中：
    - μx, μy: 图像的平均亮度
    - σx², σy²: 图像的方差（对比度）
    - σxy: 图像的协方差（结构相关性）
    - C1, C2: 稳定常数，避免除零

    优点：
    - 更接近人眼感知
    - 考虑空间结构信息
    - 纯 OpenCV 实现，无需额外依赖

    适用场景：
    - 图像质量评估
    - 压缩前后对比
    - 图像处理效果评估

    Args:
        img1: 第一张图片
        img2: 第二张图片

    Returns:
        相似度分数，范围 0-1
    """
    # 调整图片到相同尺寸（SSIM 要求）
    img1, img2 = _resize_to_same_size(img1, img2)

    # 转换为灰度图
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # 使用纯 OpenCV 实现 SSIM
    return _calculate_ssim_opencv(gray1, gray2)


def _calculate_ssim_opencv(img1: np.ndarray, img2: np.ndarray) -> float:
    """使用 OpenCV 手动实现 SSIM 计算

    这是一个纯 OpenCV 实现，不依赖 scikit-image。

    Args:
        img1: 第一张灰度图
        img2: 第二张灰度图

    Returns:
        SSIM 值，范围 0-1
    """
    # 转换为浮点数
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    # SSIM 常数，避免除零
    # C1 = (K1 * L)^2, C2 = (K2 * L)^2
    # K1 = 0.01, K2 = 0.03, L = 255 (灰度图最大值)
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    # 使用高斯滤波器计算局部均值
    # 11x11 的高斯核，标准差 1.5
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    # 计算局部均值 μx 和 μy
    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]

    # 计算均值的平方
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2

    # 计算方差和协方差
    # σx² = E[X²] - E[X]²
    sigma1_sq = cv2.filter2D(img1**2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2**2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

    # 计算 SSIM
    # SSIM = (2μxμy + C1)(2σxy + C2) / ((μx² + μy² + C1)(σx² + σy² + C2))
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
    )

    # 返回平均 SSIM
    return float(np.mean(ssim_map))


def _compare_orb(img1: np.ndarray, img2: np.ndarray) -> float:
    """ORB 特征匹配

    使用 ORB (Oriented FAST and Rotated BRIEF) 检测关键点并匹配特征描述符。
    该方法对旋转和缩放不敏感。

    原理：
    1. 特征检测：使用 ORB 检测关键点
       - FAST: 快速角点检测
       - BRIEF: 二进制描述符，计算效率高
    2. 特征匹配：使用汉明距离匹配描述符
    3. 相似度计算：综合匹配率和匹配质量

    计算公式：
    相似度 = (匹配数 / 最小特征数) * (1 - 平均距离 / 最大距离)

    优点：
    - 对旋转和缩放不敏感
    - 速度快
    - 适合物体识别

    适用场景：
    - 识别旋转或缩放的图片
    - 物体检测
    - 图像拼接

    Args:
        img1: 第一张图片
        img2: 第二张图片

    Returns:
        相似度分数，范围 0-1
    """
    # 转换为灰度图
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # 创建 ORB 特征检测器
    # nfeatures: 最多检测 500 个特征点
    orb = cv2.ORB_create(nfeatures=500)

    # 检测关键点和计算描述符
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    # 如果任一图片没有特征点，返回 0
    if des1 is None or des2 is None or len(kp1) == 0 or len(kp2) == 0:
        return 0.0

    # 使用 BFMatcher 进行特征匹配
    # NORM_HAMMING: 汉明距离，适用于 ORB 的二进制描述符
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # 如果没有匹配，返回 0
    if len(matches) == 0:
        return 0.0

    # 计算匹配率：匹配数 / 最小特征数
    match_ratio = len(matches) / min(len(kp1), len(kp2))

    # 计算平均匹配距离（距离越小越相似）
    avg_distance = sum(m.distance for m in matches) / len(matches)

    # ORB 描述符的最大汉明距离是 256（256 位）
    max_distance = 256.0

    # 综合匹配率和匹配质量计算相似度
    # 匹配质量 = 1 - (平均距离 / 最大距离)
    similarity = match_ratio * (1 - avg_distance / max_distance)

    # 确保结果在 [0, 1] 范围内
    return min(1.0, max(0.0, similarity))


def _compare_phash(img1: np.ndarray, img2: np.ndarray) -> float:
    """感知哈希 (Perceptual Hash)

    将图片转换为 64 位哈希值进行比较。该方法非常快速，适合大规模图片去重。

    原理：
    1. 缩小图片：缩小到 32x32 像素，去除细节
    2. 转换为灰度图
    3. 计算 DCT（离散余弦变换）：提取低频信息
    4. 提取左上角 8x8 的低频部分
    5. 二值化：大于平均值为 1，否则为 0
    6. 生成 64 位哈希值
    7. 计算汉明距离：两个哈希值不同位的数量

    DCT (Discrete Cosine Transform):
    - 将图像从空间域转换到频率域
    - 左上角是低频分量（图像的主要特征）
    - 右下角是高频分量（图像的细节）

    汉明距离 (Hamming Distance):
    - 两个等长字符串对应位置不同字符的个数
    - 例如：1011 和 1001 的汉明距离是 1

    优点：
    - 非常快速
    - 对轻微修改不敏感（压缩、缩放、颜色调整）
    - 适合大规模图片去重

    适用场景：
    - 查找近似重复图片
    - 图片去重
    - 版权检测

    Args:
        img1: 第一张图片
        img2: 第二张图片

    Returns:
        相似度分数，范围 0-1
    """
    # 计算两张图片的感知哈希
    hash1 = _compute_phash(img1)
    hash2 = _compute_phash(img2)

    # 计算汉明距离：不同位的数量
    hamming_distance = np.sum(hash1 != hash2)

    # 最大汉明距离是 64（64 位哈希）
    max_distance = 64.0

    # 相似度 = 1 - (汉明距离 / 最大距离)
    similarity = 1 - (hamming_distance / max_distance)

    return similarity


def _compute_phash(img: np.ndarray) -> np.ndarray:
    """计算单张图片的感知哈希值

    Args:
        img: 输入图片

    Returns:
        64 位哈希值（8x8 的二值矩阵）
    """
    # 1. 缩小到 32x32 像素
    # 去除图片细节，只保留结构信息
    resized = cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA)

    # 2. 转换为灰度图
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # 3. 计算 DCT（离散余弦变换）
    # DCT 将图像从空间域转换到频率域
    # 浮点数类型是 DCT 的要求
    dct = cv2.dct(np.float32(gray))

    # 4. 提取左上角 8x8 的低频部分
    # 低频部分包含图像的主要特征
    dct_low = dct[0:8, 0:8]

    # 5. 计算平均值（不包括 DC 分量 dct[0,0]）
    avg = np.mean(dct_low)

    # 6. 二值化：大于平均值为 1，否则为 0
    # 生成 64 位哈希值
    hash_value = dct_low > avg

    return hash_value


def _resize_to_same_size(
    img1: np.ndarray, img2: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """将两张图片调整到相同尺寸

    选择较小的尺寸作为目标尺寸，避免放大导致的质量损失。

    Args:
        img1: 第一张图片
        img2: 第二张图片

    Returns:
        调整后的两张图片
    """
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    # 选择较小的尺寸
    target_h = min(h1, h2)
    target_w = min(w1, w2)

    # 调整图片尺寸
    if (h1, w1) != (target_h, target_w):
        img1 = cv2.resize(img1, (target_w, target_h), interpolation=cv2.INTER_AREA)

    if (h2, w2) != (target_h, target_w):
        img2 = cv2.resize(img2, (target_w, target_h), interpolation=cv2.INTER_AREA)

    return img1, img2
