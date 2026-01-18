import time
from functools import wraps

from ..models.plugin import StepModel
from .context import enter_step, exit_step


class Step:
    def __init__(self, title: str):
        self.step = StepModel(name=title)

    def __enter__(self):
        self.step.start_time = int(time.time() * 1000)
        enter_step(self.step)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.step.end_time = int(time.time() * 1000)
        if exc_type:
            self.step.status = "failed"
            self.step.exception = str(exc_val)
        else:
            self.step.status = "passed"
        exit_step()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            title = self.step.name
            # If title has placeholders, format it with args/kwargs if possible
            # For simplicity, we stick to static title for now or basic format
            try:
                title = title.format(*args, **kwargs)
            except Exception:
                pass

            with Step(title):
                return func(*args, **kwargs)

        return wrapper


def step(title: str):
    return Step(title)
