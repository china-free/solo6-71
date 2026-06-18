from datetime import datetime
from collections import defaultdict
from typing import Callable, Optional

from .models import CheckResult


class Alert:
    def __init__(self, url: str, consecutive_failures: int, threshold: int,
                 last_error: str, timestamp: datetime):
        self.url = url
        self.consecutive_failures = consecutive_failures
        self.threshold = threshold
        self.last_error = last_error
        self.timestamp = timestamp
        self.resolved = False
        self.resolved_at: Optional[datetime] = None

    def resolve(self):
        self.resolved = True
        self.resolved_at = datetime.now()

    def __str__(self) -> str:
        status = "RESOLVED" if self.resolved else "TRIGGERED"
        msg = (f"[{status}] {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - "
               f"{self.url} - Consecutive failures: {self.consecutive_failures}/{self.threshold}")
        if self.last_error:
            msg += f" - Error: {self.last_error}"
        if self.resolved and self.resolved_at:
            msg += f" - Resolved at: {self.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}"
        return msg


class Alerter:
    def __init__(self, console_output: bool = True):
        self._consecutive_failures: dict[str, int] = defaultdict(int)
        self._active_alerts: dict[str, Alert] = {}
        self._alert_history: list[Alert] = []
        self.console_output = console_output
        self._on_alert_callback: Optional[Callable[[Alert], None]] = None

    def set_alert_callback(self, callback: Callable[[Alert], None]):
        self._on_alert_callback = callback

    def process_result(self, result: CheckResult, failure_threshold: int) -> Optional[Alert]:
        url = result.url

        if result.success:
            self._consecutive_failures[url] = 0
            if url in self._active_alerts:
                alert = self._active_alerts[url]
                alert.resolve()
                del self._active_alerts[url]
                self._alert_history.append(alert)
                if self.console_output:
                    print(f"\n⚠️  {alert}")
                if self._on_alert_callback:
                    self._on_alert_callback(alert)
                return alert
        else:
            self._consecutive_failures[url] += 1
            consecutive = self._consecutive_failures[url]

            if consecutive >= failure_threshold and url not in self._active_alerts:
                alert = Alert(
                    url=url,
                    consecutive_failures=consecutive,
                    threshold=failure_threshold,
                    last_error=result.error_message or "Unknown error",
                    timestamp=datetime.now()
                )
                self._active_alerts[url] = alert
                self._alert_history.append(alert)
                if self.console_output:
                    print(f"\n🚨 {alert}")
                if self._on_alert_callback:
                    self._on_alert_callback(alert)
                return alert

        return None

    def get_active_alerts(self) -> list[Alert]:
        return list(self._active_alerts.values())

    def get_alert_history(self) -> list[Alert]:
        return self._alert_history.copy()

    def get_consecutive_failures(self, url: str) -> int:
        return self._consecutive_failures.get(url, 0)
