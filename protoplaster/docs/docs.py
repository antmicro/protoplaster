from dataclasses import dataclass
from typing import List


@dataclass
class TestDocs:
    class_name: str
    test_details: List[str]
    test_macros: List[str]
