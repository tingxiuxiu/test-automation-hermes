from pydantic import BaseModel

from .component import Box, Point


class OCRItem(BaseModel):
    text: str
    box: Box
    center: Point
    threshold: float
