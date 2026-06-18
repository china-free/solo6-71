import csv
import os
from datetime import datetime
from typing import Optional

from .models import CheckResult
from .statistics import StatisticsReporter


class CSVExporter:
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def export_results(self, results: list[CheckResult],
                       filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"monitoring_results_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CheckResult.csv_headers())
            for result in results:
                writer.writerow(result.to_csv_row())

        return filepath

    def export_url_results(self, url: str, results: list[CheckResult],
                           filename: Optional[str] = None) -> str:
        url_results = [r for r in results if r.url == url]
        if filename is None:
            safe_url = url.replace('://', '_').replace('/', '_').replace(':', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_url}_{timestamp}.csv"
        return self.export_results(url_results, filename)

    def export_from_reporter(self, reporter: StatisticsReporter,
                             filename: Optional[str] = None) -> str:
        all_results = []
        for url in reporter.get_all_urls():
            stats = reporter.get_url_stats(url)
            if stats:
                all_results.extend(stats.results)
        return self.export_results(all_results, filename)


class ConsoleExporter:
    @staticmethod
    def print_result(result: CheckResult, consecutive_failures: int = 0):
        status_icon = "✅" if result.success else "❌"
        status_code = result.status_code if result.status_code is not None else "N/A"
        timestamp = result.timestamp.strftime('%Y-%m-%d %H:%M:%S')

        line = (f"{status_icon} {timestamp} | {result.url:<50} | "
                f"Status: {status_code:<5} | Time: {result.response_time:.3f}s")

        if consecutive_failures > 0:
            line += f" | Consecutive failures: {consecutive_failures}"

        if result.error_message and not result.success:
            line += f" | Error: {result.error_message}"

        print(line)
