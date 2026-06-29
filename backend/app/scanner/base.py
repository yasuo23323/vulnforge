from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ScanResult:
    scanner_name: str = ""
    vulnerability_type: str = ""
    severity: str = "medium"
    url: str = ""
    request_data: str = ""
    response_data: str = ""
    raw_evidence: str = ""
    description: str = ""
    extra_data: dict = field(default_factory=dict)
    raw_output: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseScanner(ABC):
    def __init__(self, binary_path: str = ""):
        self.binary_path = binary_path

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def run(self, target_url: str) -> list[ScanResult]:
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> list[ScanResult]:
        ...