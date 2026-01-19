from itertools import chain
import pytest
import csv
import io


class CsvReportGenerator:

    def __init__(self, columns, metadata):
        self.columns = columns
        self.report = []
        self.retrieve_field = {
            "device name": (lambda item, report: dict(item.user_properties).
                            get("device", "unknown device")),
            "test name":
            (lambda item, report: item.name.removeprefix("test_")),
            "module":
            (lambda item, report: report.nodeid[report.nodeid.find("test.py"):]
             ),
            "duration": (lambda item, report: report.duration),
            "message": (lambda item, report: self.get_test_message(report)),
            "status": (lambda item, report: report.outcome),
            "artifacts": (lambda item, report: list(
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
        else:
            return ""

    @pytest.mark.hookwrapper
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()

        if report.when != 'call' and report.passed:
            return

        row = [
            self.retrieve_field[column](item, report)
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
