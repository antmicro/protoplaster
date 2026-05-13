from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hint:
    description: str
    name: str = ""
    required: bool = False
    children: list["Hint"] = field(default_factory=list)
    datatype: str = ""


@dataclass
class TestDocs:
    class_name: str
    test_details: dict[str, Any]
    test_macros: list[str]
