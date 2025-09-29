from enum import Enum
from datetime import datetime
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
        "test_suite_name": test_suite_name,
        "status": RunStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
    }
