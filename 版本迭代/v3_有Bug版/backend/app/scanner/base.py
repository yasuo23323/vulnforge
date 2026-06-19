from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class ScanResult:
    scanner_name: str
    vulnerability_type: str
    severity: str  # critical, high, medium, low, info
    url: str
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    raw_evidence: Optional[str] = None
    description: Optional[str] = None
    extra_data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseScanner(ABC):
    """Abstract base class for all vulnerability scanners."""

    def __init__(self, binary_path: str):
        self.binary_path = binary_path

    @property
    @abstractmethod
    def name(self) -> str:
        """Scanner identifier (e.g., 'nuclei', 'sqlmap')."""
        pass

    @abstractmethod
    async def scan(self, target_url: str, **kwargs) -> list[ScanResult]:
        """Run scanner against target URL and return structured results."""
        pass

    @abstractmethod
    def parse_output(self, raw_output: str) -> list[ScanResult]:
        """Parse raw scanner output into structured ScanResult objects."""
        pass
