from pydantic import BaseModel


class Size(BaseModel):
    width: int
    height: int


class Point(BaseModel):
    x: int
    y: int


class Box(BaseModel):
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int


class Component(BaseModel):
    name: str
    size: Size
    point: Point
    box: Box
