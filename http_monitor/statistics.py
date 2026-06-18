from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

from .models import CheckResult


class URLStatistics:
    def __init__(self, url: str):
        self.url = url
        self.results: list[CheckResult] = []

    def add_result(self, result: CheckResult):
        self.results.append(result)

    def avg_response_time(self, results: Optional[list[CheckResult]] = None) -> float:
        target_results = results if results is not None else self.results
        if not target_results:
            return 0.0
        total_time = sum(r.response_time for r in target_results)
        return total_time / len(target_results)

    def success_rate(self, results: Optional[list[CheckResult]] = None) -> float:
        target_results = results if results is not None else self.results
        if not target_results:
            return 0.0
        successful = sum(1 for r in target_results if r.success)
        return (successful / len(target_results)) * 100

    def availability_24h(self) -> float:
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        recent_results = [r for r in self.results if r.timestamp >= twenty_four_hours_ago]
        return self.success_rate(recent_results)

    def total_checks(self) -> int:
        return len(self.results)

    def successful_checks(self) -> int:
        return sum(1 for r in self.results if r.success)

    def failed_checks(self) -> int:
        return sum(1 for r in self.results if not r.success)

    def min_response_time(self) -> float:
        if not self.results:
            return 0.0
        return min(r.response_time for r in self.results)

    def max_response_time(self) -> float:
        if not self.results:
            return 0.0
        return max(r.response_time for r in self.results)

    def get_recent_results(self, hours: int = 24) -> list[CheckResult]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [r for r in self.results if r.timestamp >= cutoff]


class StatisticsReporter:
    def __init__(self):
        self._url_stats: dict[str, URLStatistics] = defaultdict(lambda: URLStatistics(""))

    def add_result(self, result: CheckResult):
        if result.url not in self._url_stats:
            self._url_stats[result.url] = URLStatistics(result.url)
        self._url_stats[result.url].add_result(result)

    def get_url_stats(self, url: str) -> Optional[URLStatistics]:
        return self._url_stats.get(url)

    def get_all_urls(self) -> list[str]:
        return list(self._url_stats.keys())

    def generate_report(self) -> str:
        lines = [
            "=" * 80,
            "HTTP MONITORING STATISTICS REPORT",
            "=" * 80,
            f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        for url in self.get_all_urls():
            stats = self._url_stats[url]
            lines.extend([
                f"URL: {url}",
                "-" * 80,
                f"  Total checks:        {stats.total_checks()}",
                f"  Successful:          {stats.successful_checks()}",
                f"  Failed:              {stats.failed_checks()}",
                f"  Success rate:        {stats.success_rate():.2f}%",
                f"  24h Availability:    {stats.availability_24h():.2f}%",
                f"  Avg response time:   {stats.avg_response_time():.3f}s",
                f"  Min response time:   {stats.min_response_time():.3f}s",
                f"  Max response time:   {stats.max_response_time():.3f}s",
                ""
            ])

        lines.append("=" * 80)
        return "\n".join(lines)

    def print_report(self):
        print(self.generate_report())
