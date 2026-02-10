from pydantic import BaseModel


class Size(BaseModel):
    width: int
    height: int


class Point(BaseModel):
    x: int
    y: int


class Bounds(BaseModel):
    left: int
    top: int
    right: int
    bottom: int
