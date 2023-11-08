import pytest
import csv


def pytest_addoption(parser):
    parser.addoption("--csv-output",
                     action="store",
                     type=str,
                     help="csv report output file")
    parser.addoption("--csv-columns",
                     action="store",
                     type=str,
                     help="csv report columns")


csv_report_file = None  # there is no clean way to store this between hooks invocations, because in pytest_configure we only have access to `config`
csv_columns = []
csv_report = []


def get_test_message(report):
    if hasattr(report.longrepr, "reprcrash") and hasattr(
            report.longrepr.reprcrash, "message"):
        return report.longrepr.reprcrash.message
    else:
        return ""


retrieve_field = {
    "device name": (lambda item, report: dict(item.user_properties).get(
        "device", "unknown device")),
    "test name": (lambda item, report: item.name.removeprefix("test_")),
    "module":
    (lambda item, report: report.nodeid[report.nodeid.find("test.py"):]),
    "duration": (lambda item, report: report.duration),
    "message": (lambda item, report: get_test_message(report)),
    "status": (lambda item, report: report.outcome)
}


def pytest_configure(config):
    global csv_report_file
    global csv_columns

    csv_report_file = config.option.csv_output
    if config.option.csv_columns:
        csv_columns = config.option.csv_columns.replace(" ", "").replace(
            "_", " ").split(",")
        csv_columns = list(filter(lambda c: c in retrieve_field, csv_columns))
    else:
        csv_columns = retrieve_field.keys()


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != 'call' and report.passed:
        return

    row = [retrieve_field[column](item, report) for column in csv_columns]
    csv_report.append(row)


def pytest_sessionfinish(session):
    if csv_report_file != None:
        with open(csv_report_file, "w") as out:
            writer = csv.writer(out)
            writer.writerow(csv_columns)
            for row in csv_report:
                writer.writerow(row)
