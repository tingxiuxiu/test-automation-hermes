"""
测试图片相似度对比功能的示例脚本

使用方法:
1. 准备两张图片
2. 运行脚本查看相似度分数
"""

from pathlib import Path

from hermes._media.image_calc import compare_similarity
from hermes.models.selector import SimilarityAlgorithm


def test_histogram_comparison():
    """测试直方图比较"""

    image1_path = Path("path/to/image1.png")
    image2_path = Path("path/to/image2.png")

    score = compare_similarity(
        image1_path, image2_path, algorithm=SimilarityAlgorithm.HISTOGRAM
    )

    print(f"直方图比较相似度: {score:.3f}")


def test_ssim_comparison():
    """测试 SSIM 结构相似度"""

    image1_path = Path("path/to/image1.png")
    image2_path = Path("path/to/image2.png")

    score = compare_similarity(
        image1_path, image2_path, algorithm=SimilarityAlgorithm.SSIM
    )

    print(f"SSIM 相似度: {score:.3f}")


def test_orb_comparison():
    """测试 ORB 特征匹配"""

    image1_path = Path("path/to/image1.png")
    image2_path = Path("path/to/image2.png")

    score = compare_similarity(
        image1_path, image2_path, algorithm=SimilarityAlgorithm.ORB
    )

    print(f"ORB 特征匹配相似度: {score:.3f}")


def test_phash_comparison():
    """测试感知哈希"""

    image1_path = Path("path/to/image1.png")
    image2_path = Path("path/to/image2.png")

    score = compare_similarity(
        image1_path, image2_path, algorithm=SimilarityAlgorithm.PHASH
    )

    print(f"感知哈希相似度: {score:.3f}")


def test_all_algorithms():
    """测试所有算法"""

    image1_path = Path("path/to/image1.png")
    image2_path = Path("path/to/image2.png")

    print("=" * 60)
    print("图片相似度对比测试")
    print("=" * 60)

    algorithms = [
        (SimilarityAlgorithm.HISTOGRAM, "直方图比较"),
        (SimilarityAlgorithm.SSIM, "SSIM 结构相似度"),
        (SimilarityAlgorithm.ORB, "ORB 特征匹配"),
        (SimilarityAlgorithm.PHASH, "感知哈希"),
    ]

    for algo, name in algorithms:
        score = compare_similarity(image1_path, image2_path, algorithm=algo)
        print(f"{name:20s}: {score:.3f}")


if __name__ == "__main__":
    # 运行测试
    print("=" * 60)
    print("图片相似度对比功能测试")
    print("=" * 60)

    # 取消注释以运行相应的测试
    # test_histogram_comparison()
    # test_ssim_comparison()
    # test_orb_comparison()
    # test_phash_comparison()
    # test_all_algorithms()

    print("\n请修改图片路径后运行测试")
