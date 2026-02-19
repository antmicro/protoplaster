from dataclasses import dataclass
from typing import Any


@dataclass
class TestDocs:
    class_name: str
    test_details: dict[str, Any]
    test_macros: list[str]
