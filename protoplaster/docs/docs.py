from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hint:
    description: str
    name: str = ""
    required: bool = False
    children: list["Hint"] = field(default_factory=list)
    datatype: str = ""
    hidden: bool = False


@dataclass
class TestDocs:
    class_name: str
    parameters: list[Hint]
    test_details: dict[str, Any]
    test_macros: list[str]
