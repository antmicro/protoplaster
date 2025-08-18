import pytest
from os import getpid
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LogGenerator:

    def __init__(self, log_path):
        self.report = []
        self.retrieve_field = {
            "device_name": (lambda item, report: dict(item.user_properties).
                            get("device", "unknown")),
            "test_name":
            (lambda item, report: item.name.removeprefix("test_")),
            "module":
            (lambda item, report: report.nodeid[report.nodeid.find("test.py"):]
             ),
            "duration": (lambda item, report: round(report.duration, 4)),
            "message": (lambda item, report: self.get_test_message(report)),
            "status": (lambda item, report: report.outcome),
            "user_properties": (lambda item, report: {
                prop[0]: prop[1]
                for prop in report.user_properties[1:]
            }),
        }

        self.keys = self.retrieve_field.keys()

        handler = RotatingFileHandler(log_path,
                                      maxBytes=10 * 1024 * 1024,
                                      backupCount=5)
        formatter = logging.Formatter("%(created)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def get_test_message(self, report):
        if hasattr(report.longrepr, "reprcrash") and hasattr(
                report.longrepr.reprcrash, "message"):
            return report.longrepr.reprcrash.message
        else:
            return ""

    @pytest.mark.hookwrapper
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()

        if report.when != "call" and report.passed:
            return

        log = {
            key: self.retrieve_field[key](item, report)
            for key in self.retrieve_field.keys()
        }

        logger.info(f"[{getpid()}] {str(log)}")
