from typing import Union


class StatusClassifier:
    def __init__(self, success_ranges: Union[list[tuple[int, int]], None] = None):
        if success_ranges is None:
            success_ranges = [(200, 299)]
        self.success_ranges = success_ranges

    @classmethod
    def from_config(cls, config: Union[dict, list, None] = None) -> 'StatusClassifier':
        if config is None:
            return cls()

        if isinstance(config, list):
            ranges = []
            for item in config:
                if isinstance(item, int):
                    ranges.append((item, item))
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    ranges.append((int(item[0]), int(item[1])))
                else:
                    raise ValueError(f"Invalid status code range: {item}")
            return cls(ranges)

        if isinstance(config, dict):
            if 'success_codes' in config:
                return cls.from_config(config['success_codes'])
            if 'success_range' in config:
                r = config['success_range']
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    return cls([(int(r[0]), int(r[1]))])

        raise ValueError(f"Invalid status classifier config: {config}")

    def is_success(self, status_code: int) -> bool:
        if status_code is None:
            return False
        for start, end in self.success_ranges:
            if start <= status_code <= end:
                return True
        return False

    def classify(self, status_code: int) -> str:
        if status_code is None:
            return 'UNKNOWN'
        if self.is_success(status_code):
            return 'SUCCESS'
        if 300 <= status_code < 400:
            return 'REDIRECT'
        if 400 <= status_code < 500:
            return 'CLIENT_ERROR'
        if 500 <= status_code < 600:
            return 'SERVER_ERROR'
        return 'OTHER'

    def get_success_ranges_str(self) -> str:
        parts = []
        for start, end in self.success_ranges:
            if start == end:
                parts.append(str(start))
            else:
                parts.append(f"{start}-{end}")
        return ", ".join(parts)

    def __str__(self) -> str:
        return f"StatusClassifier(success=[{self.get_success_ranges_str()}])"

    def __repr__(self) -> str:
        return self.__str__()
