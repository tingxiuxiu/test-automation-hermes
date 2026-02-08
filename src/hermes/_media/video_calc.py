from pathlib import Path
from typing import Sequence

from ..models.component import Point, Bounds, Size, ImageModal
from ..models.selector import ImageSelector


class VideoCalc:
    def loactor(self, target: ImageSelector, source: Path) -> ImageModal:
        return ImageModal(
            tag="",
            bounds=Bounds(left=0, top=0, right=0, bottom=0),
            size=Size(width=0, height=0),
            center=Point(x=0, y=0),
        )

    def locators(self, target: ImageSelector, source: Path) -> Sequence[ImageModal]:
        return []
