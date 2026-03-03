from itertools import chain
import pytest
import csv
import io
from datetime import datetime


class CsvReportGenerator:

    def __init__(self, columns, metadata):
        self.columns = columns
        self.report = []
        self.retrieve_field = {
            "start time": (lambda item, report, call: datetime.fromtimestamp(
                call.start).isoformat(timespec="seconds")),
            "device name":
            (lambda item, report, call: item.cls.name(item.instance)),
            "test name":
            (lambda item, report, call: item.name.removeprefix("test_")),
            "module": (lambda item, report, call: report.nodeid[
                report.nodeid.find("test.py"):]),
            "duration": (lambda item, report, call: report.duration),
            "message":
            (lambda item, report, call: self.get_test_message(report)),
            "status": (lambda item, report, call: report.outcome),
            "artifacts": (lambda item, report, call: list(
                chain(getattr(item, "_artifacts", []), metadata)))
        }
        if columns:
            self.columns = self.columns.replace(" ",
                                                "").replace("_",
                                                            " ").split(",")
        else:
            self.columns = self.retrieve_field.keys()

    def get_test_message(self, report):
        if hasattr(report.longrepr, "reprcrash") and hasattr(
                report.longrepr.reprcrash, "message"):
            msg = report.longrepr.reprcrash.message
            return msg.split("\nassert")[0]
        elif report.skipped and isinstance(report.longrepr, tuple):
            return report.longrepr[2]
        return ""

    @pytest.mark.hookwrapper
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()

        if report.when != 'call' and report.passed:
            return

        row = [
            self.retrieve_field[column](item, report, call)
            for column in self.columns
        ]
        self.report.append(row)

    def pytest_sessionfinish(self, session):
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(self.columns)
        for row in self.report:
            writer.writerow(row)
        self.report = out.getvalue()
