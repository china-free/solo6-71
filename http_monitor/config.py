import os
from typing import Optional
import yaml

from .models import MonitorConfig, URLConfig


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
                       failure_threshold: int = 3, timeout: int = 10) -> MonitorConfig:
        url_configs = [
            URLConfig(url=url, interval=interval, failure_threshold=failure_threshold, timeout=timeout)
            for url in urls
        ]
        return MonitorConfig(
            urls=url_configs,
            default_interval=interval,
            default_failure_threshold=failure_threshold,
            default_timeout=timeout
        )

    @staticmethod
    def _parse_config(raw_config: dict) -> MonitorConfig:
        defaults = raw_config.get('defaults', {})
        default_interval = defaults.get('interval', 60)
        default_failure_threshold = defaults.get('failure_threshold', 3)
        default_timeout = defaults.get('timeout', 10)
        export_interval = defaults.get('export_interval', 300)
        report_interval = defaults.get('report_interval', 600)

        url_configs = []
        for url_entry in raw_config.get('urls', []):
            if isinstance(url_entry, str):
                url_configs.append(URLConfig(
                    url=url_entry,
                    interval=default_interval,
                    failure_threshold=default_failure_threshold,
                    timeout=default_timeout
                ))
            elif isinstance(url_entry, dict):
                url_configs.append(URLConfig(
                    url=url_entry['url'],
                    interval=url_entry.get('interval', default_interval),
                    failure_threshold=url_entry.get('failure_threshold', default_failure_threshold),
                    timeout=url_entry.get('timeout', default_timeout),
                    method=url_entry.get('method', 'GET')
                ))

        return MonitorConfig(
            urls=url_configs,
            default_interval=default_interval,
            default_failure_threshold=default_failure_threshold,
            default_timeout=default_timeout,
            export_interval=export_interval,
            report_interval=report_interval
        )
