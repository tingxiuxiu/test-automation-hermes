from datetime import datetime

from pydantic import BaseModel


class LogcatItem(BaseModel):
    timestamp: datetime
    message: str
