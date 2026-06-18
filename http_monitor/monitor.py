import time
import requests
from typing import Callable, Optional

from .models import CheckResult, URLConfig
from .classifier import StatusClassifier


class HTTPMonitor:
    def __init__(self, url_config: URLConfig):
        self.url_config = url_config
        self._classifier: StatusClassifier = url_config.get_status_classifier()
        self._last_check_time: Optional[float] = None

    @property
    def classifier(self) -> StatusClassifier:
        return self._classifier

    def check(self) -> CheckResult:
        url = self.url_config.url
        method = self.url_config.method
        timeout = self.url_config.timeout

        start_time = time.time()
        status_code = None
        success = False
        error_message = None

        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=timeout,
                allow_redirects=True
            )
            status_code = response.status_code
            success = self._classifier.is_success(status_code)
            if not success:
                category = self._classifier.classify(status_code)
                error_message = f"HTTP {status_code} ({category})"
        except requests.exceptions.Timeout:
            error_message = "Request timed out"
        except requests.exceptions.ConnectionError as e:
            error_message = f"Connection error: {str(e)}"
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {str(e)}"
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"

        response_time = time.time() - start_time
        self._last_check_time = time.time()

        return CheckResult(
            url=url,
            status_code=status_code,
            response_time=response_time,
            success=success,
            error_message=error_message
        )

    @property
    def interval(self) -> int:
        return self.url_config.interval

    @property
    def url(self) -> str:
        return self.url_config.url

    @property
    def failure_threshold(self) -> int:
        return self.url_config.failure_threshold
