from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class CheckResult:
    url: str
    status_code: Optional[int]
    response_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return data

    def to_csv_row(self) -> list:
        return [
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.url,
            self.status_code if self.status_code is not None else 'N/A',
            f"{self.response_time:.3f}",
            'SUCCESS' if self.success else 'FAILURE',
            self.error_message if self.error_message else ''
        ]

    @staticmethod
    def csv_headers() -> list:
        return ['timestamp', 'url', 'status_code', 'response_time_seconds', 'result', 'error_message']


@dataclass
class URLConfig:
    url: str
    interval: int = 60
    failure_threshold: int = 3
    timeout: int = 10
    method: str = 'GET'


@dataclass
class MonitorConfig:
    urls: list[URLConfig]
    default_interval: int = 60
    default_failure_threshold: int = 3
    default_timeout: int = 10
    export_interval: int = 300
    report_interval: int = 600
