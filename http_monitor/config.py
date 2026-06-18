import os
from typing import Optional
import yaml

from .models import MonitorConfig, URLConfig
from .classifier import StatusClassifier


class ConfigLoader:
    @staticmethod
    def load_from_yaml(config_path: str) -> MonitorConfig:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        return ConfigLoader._parse_config(raw_config)

    @staticmethod
    def load_from_args(urls: list[str], interval: int = 60,
                       failure_threshold: int = 3, timeout: int = 10,
                       success_ranges: Optional[list[tuple[int, int]]] = None) -> MonitorConfig:
        if success_ranges is None:
            success_ranges = [(200, 299)]

        url_configs = [
            URLConfig(
                url=url,
                interval=interval,
                failure_threshold=failure_threshold,
                timeout=timeout,
                success_ranges=success_ranges
            )
            for url in urls
        ]
        return MonitorConfig(
            urls=url_configs,
            default_interval=interval,
            default_failure_threshold=failure_threshold,
            default_timeout=timeout,
            default_success_ranges=success_ranges
        )

    @staticmethod
    def _parse_success_ranges(config_value) -> list[tuple[int, int]]:
        if config_value is None:
            return [(200, 299)]

        if isinstance(config_value, list):
            ranges = []
            for item in config_value:
                if isinstance(item, int):
                    ranges.append((item, item))
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    ranges.append((int(item[0]), int(item[1])))
                elif isinstance(item, str):
                    if '-' in item:
                        start, end = item.split('-', 1)
                        ranges.append((int(start.strip()), int(end.strip())))
                    else:
                        ranges.append((int(item.strip()), int(item.strip())))
                else:
                    raise ValueError(f"Invalid status code range: {item}")
            return ranges

        raise ValueError(f"Invalid success_ranges config: {config_value}")

    @staticmethod
    def _parse_config(raw_config: dict) -> MonitorConfig:
        defaults = raw_config.get('defaults', {})
        default_interval = defaults.get('interval', 60)
        default_failure_threshold = defaults.get('failure_threshold', 3)
        default_timeout = defaults.get('timeout', 10)
        default_success_ranges = ConfigLoader._parse_success_ranges(
            defaults.get('success_ranges', None)
        )
        export_interval = defaults.get('export_interval', 300)
        report_interval = defaults.get('report_interval', 600)

        url_configs = []
        for url_entry in raw_config.get('urls', []):
            if isinstance(url_entry, str):
                url_configs.append(URLConfig(
                    url=url_entry,
                    interval=default_interval,
                    failure_threshold=default_failure_threshold,
                    timeout=default_timeout,
                    success_ranges=default_success_ranges
                ))
            elif isinstance(url_entry, dict):
                url_success_ranges = default_success_ranges
                if 'success_ranges' in url_entry:
                    url_success_ranges = ConfigLoader._parse_success_ranges(
                        url_entry['success_ranges']
                    )

                url_configs.append(URLConfig(
                    url=url_entry['url'],
                    interval=url_entry.get('interval', default_interval),
                    failure_threshold=url_entry.get('failure_threshold', default_failure_threshold),
                    timeout=url_entry.get('timeout', default_timeout),
                    method=url_entry.get('method', 'GET'),
                    success_ranges=url_success_ranges
                ))

        return MonitorConfig(
            urls=url_configs,
            default_interval=default_interval,
            default_failure_threshold=default_failure_threshold,
            default_timeout=default_timeout,
            default_success_ranges=default_success_ranges,
            export_interval=export_interval,
            report_interval=report_interval
        )
