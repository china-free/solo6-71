#!/usr/bin/env python3
import argparse
import time
import signal
import sys
from datetime import datetime
from typing import Optional

from http_monitor.config import ConfigLoader
from http_monitor.models import MonitorConfig
from http_monitor.monitor import HTTPMonitor
from http_monitor.alerter import Alerter
from http_monitor.statistics import StatisticsReporter
from http_monitor.exporter import CSVExporter, ConsoleExporter


class HTTPMonitoringService:
    def __init__(self, config: MonitorConfig, export_dir: str = "exports"):
        self.config = config
        self.monitors = [HTTPMonitor(url_config) for url_config in config.urls]
        self.alerter = Alerter(console_output=True)
        self.reporter = StatisticsReporter()
        self.csv_exporter = CSVExporter(output_dir=export_dir)
        self.console_exporter = ConsoleExporter()
        self._running = False
        self._last_export_time: Optional[float] = None
        self._last_report_time: Optional[float] = None
        self._all_results = []

        self._register_signal_handlers()

    def _register_signal_handlers(self):
        def handle_signal(signum, frame):
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            self.stop()
            self._print_final_report()
            self._export_final_data()
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

    def start(self):
        self._running = True
        print("=" * 80)
        print("HTTP Service Availability Monitor")
        print("=" * 80)
        print(f"Monitoring {len(self.monitors)} URLs:")
        for monitor in self.monitors:
            print(f"  - {monitor.url} (interval: {monitor.interval}s, "
                  f"threshold: {monitor.failure_threshold} failures)")
        print("=" * 80)
        print("Press Ctrl+C to stop\n")

        while self._running:
            self._check_all_urls()
            self._check_periodic_tasks()
            time.sleep(1)

    def stop(self):
        self._running = False

    def _check_all_urls(self):
        current_time = time.time()

        for monitor in self.monitors:
            if self._should_check(monitor, current_time):
                self._check_single_url(monitor)

    def _should_check(self, monitor: HTTPMonitor, current_time: float) -> bool:
        if monitor._last_check_time is None:
            return True
        return (current_time - monitor._last_check_time) >= monitor.interval

    def _check_single_url(self, monitor: HTTPMonitor):
        result = monitor.check()
        self._all_results.append(result)
        self.reporter.add_result(result)

        alert = self.alerter.process_result(result, monitor.failure_threshold)
        consecutive_failures = self.alerter.get_consecutive_failures(monitor.url)

        self.console_exporter.print_result(result, consecutive_failures)

    def _check_periodic_tasks(self):
        current_time = time.time()

        if self._last_export_time is None or \
           (current_time - self._last_export_time) >= self.config.export_interval:
            self._export_data()
            self._last_export_time = current_time

        if self._last_report_time is None or \
           (current_time - self._last_report_time) >= self.config.report_interval:
            self.reporter.print_report()
            self._last_report_time = current_time

    def _export_data(self):
        if not self._all_results:
            return

        filepath = self.csv_exporter.export_results(self._all_results)
        print(f"\n📊 Data exported to: {filepath}")

    def _print_final_report(self):
        print("\n" + "=" * 80)
        print("FINAL MONITORING REPORT")
        print("=" * 80)
        self.reporter.print_report()

    def _export_final_data(self):
        if self._all_results:
            filepath = self.csv_exporter.export_results(
                self._all_results,
                filename=f"final_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            print(f"\n💾 Final data exported to: {filepath}\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="HTTP Service Availability Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url https://example.com --url https://google.com -i 30
  %(prog)s -c config.yaml
  %(prog)s --url https://example.com -t 10 --failure-threshold 5
        """
    )

    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument("-c", "--config", type=str,
                              help="Path to YAML configuration file")

    url_group = parser.add_argument_group("URL Configuration")
    url_group.add_argument("--url", action="append", type=str,
                           help="URL to monitor (can be specified multiple times)")
    url_group.add_argument("-i", "--interval", type=int, default=60,
                           help="Check interval in seconds (default: 60)")
    url_group.add_argument("-t", "--timeout", type=int, default=10,
                           help="Request timeout in seconds (default: 10)")
    url_group.add_argument("--failure-threshold", type=int, default=3,
                           help="Consecutive failures before alert (default: 3)")

    export_group = parser.add_argument_group("Export Configuration")
    export_group.add_argument("--export-dir", type=str, default="exports",
                              help="Directory for CSV exports (default: exports)")
    export_group.add_argument("--export-interval", type=int, default=300,
                              help="Export interval in seconds (default: 300)")
    export_group.add_argument("--report-interval", type=int, default=600,
                              help="Statistics report interval in seconds (default: 600)")

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        if args.config:
            config = ConfigLoader.load_from_yaml(args.config)
        elif args.url:
            config = ConfigLoader.load_from_args(
                urls=args.url,
                interval=args.interval,
                failure_threshold=args.failure_threshold,
                timeout=args.timeout
            )
            config.export_interval = args.export_interval
            config.report_interval = args.report_interval
        else:
            print("Error: You must specify either --config or --url")
            print("Use --help for more information.")
            sys.exit(1)

        if not config.urls:
            print("Error: No URLs configured to monitor")
            sys.exit(1)

        service = HTTPMonitoringService(config, export_dir=args.export_dir)
        service.start()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
