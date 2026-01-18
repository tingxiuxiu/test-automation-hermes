import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class ReportModel(BaseModel):
    uuid: str
    case_num: int = 0
    random_seed: int = -1
    actual_run_num: int = 0
    passed_num: int = 0
    skipped_num: int = 0
    failed_num: int = 0
    broken_num: int = 0
    no_know_exception_num: int = 0
    start_time: int = int(time.time() * 1000)
    end_time: int = int(time.time() * 1000)


class PluginOptions(BaseModel):
    hermes_uuid: str
    hermes_random_seed: int
    hermes_device_check: bool


class StepModel(BaseModel):
    name: str
    start_time: int = int(time.time() * 1000)
    end_time: int = 0
    status: Literal["passed", "skipped", "failed", "broken", "no_know_exception"] = (
        "passed"
    )
    exception: str | None = None
    steps: list[StepModel] = []


class CaseModel(BaseModel):
    case_id: str
    start_time: int = int(time.time() * 1000)
    end_time: int = int(time.time() * 1000)
    result: Literal["passed", "skipped", "failed", "broken", "no_know_exception"] = (
        "passed"
    )
    execption: str | None = None
    screenshot: Path | None = None
    video: Path | None = None
    logger: Path | None = None
    steps: list[StepModel] = []
