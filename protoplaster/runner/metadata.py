from enum import Enum
from datetime import datetime, timezone
from email.utils import format_datetime
import uuid


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    ABORTED = "aborted"


def new_run_metadata(config_name, test_suite_name):
    return {
        "id": str(uuid.uuid4()),
        "config_name": config_name,
        "test_suite_name": "" if test_suite_name is None else test_suite_name,
        "status": RunStatus.PENDING,
        "created_at": format_datetime(datetime.now(timezone.utc)),
        "started_at": "",
        "finished_at": "",
        "metadata": dict(),
    }
