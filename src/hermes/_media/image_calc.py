import time
from pathlib import Path
from typing import Sequence

from ..models.component import Point, Bounds, Size, ImageModal
from ..protocol.driver_protocol import DriverProtocol


class ImageCalc:
    def wait_for(
        self,
        target: Path,
        *,
        driver: DriverProtocol,
        threshold: float = 0.95,
        visible: bool = True,
        timeout: int = 15000,
    ) -> Sequence[ImageModal]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            if visible:
                return [
                    ImageModal(
                        tag="",
                        bounds=Bounds(left=0, top=0, right=0, bottom=0),
                        size=Size(width=0, height=0),
                        center=Point(x=0, y=0),
                    )
                ]
            else:
                return []
        return []
