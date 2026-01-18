import time

from pytest import CallInfo, Item, hookimpl

from .._core.context import clear_context, init_context
from ..models.plugin import CaseModel


class CaseListener:
    def pytest_runtest_logstart(
        self, nodeid: str, location: tuple[str, int | None, str | None]
    ):
        self.case = CaseModel(case_id=nodeid, start_time=int(time.time() * 1000))
        init_context(self.case)

    def pytest_runtest_logfinish(
        self, nodeid: str, location: tuple[str, int | None, str | None]
    ):
        self.case.end_time = int(time.time() * 1000)
        clear_context()

    @hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo[None]):
        outcome = yield
        report = outcome.get_result()
        if report.passed:
            self.case.result = "passed"
        elif report.skipped:
            self.case.result = "skipped"
        elif report.failed:
            self.case.result = "failed"
        elif report.broken:
            self.case.result = "broken"
        else:
            self.case.result = "no_know_exception"
