from dataclasses import dataclass
from typing import List

@dataclass
class TestDocs:
    test_class_name: str
    test_method: List[str]
