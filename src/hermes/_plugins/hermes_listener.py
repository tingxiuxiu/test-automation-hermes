import time

from pytest import CallInfo, Item, Session, hookimpl

from ..models.plugin import PluginOptions, ReportModel


class HermesListener:
    def __init__(self, options: PluginOptions):
        self.options = options
        self.report = ReportModel(
            uuid=options.hermes_uuid, random_seed=options.hermes_random_seed
        )

    def pytest_collection_modifyitems(self, items: list[Item]):
        self.report.case_num = len(items)

    def pytest_sessionstart(self, session: Session):
        self.report.start_time = int(time.time() * 1000)

    def pytest_runtest_logstart(
        self, nodeid: str, location: tuple[str, int | None, str | None]
    ):
        self.report.actual_run_num += 1

    def pytest_runtest_logfinish(
        self, nodeid: str, location: tuple[str, int | None, str | None]
    ): ...

    @hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo[None]):
        outcome = yield
        report = outcome.get_result()
        if report.passed:
            self.report.passed_num += 1
        elif report.skipped:
            self.report.skipped_num += 1
        elif report.failed:
            self.report.failed_num += 1
        elif report.broken:
            self.report.broken_num += 1
        else:
            self.report.no_know_exception_num += 1

    def pytest_sessionfinish(self, session: Session):
        self.report.end_time = int(time.time() * 1000)
