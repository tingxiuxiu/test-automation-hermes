from pydantic import BaseModel

from .component import Bounds, Point


class OCRItem(BaseModel):
    text: str
    bounds: Bounds
    center: Point
    threshold: float
