from dataclasses import dataclass
from typing import List

@dataclass
class TestMacro:
    test_macro_file: str
    test_macro_name: str

@dataclass
class TestDocs:
    class_macros: List[TestMacro]
    test_details: List[str]
    test_macros: List[TestMacro]
