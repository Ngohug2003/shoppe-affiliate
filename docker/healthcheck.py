from __future__ import annotations

import sys
import urllib.error
import urllib.request


def main() -> int:
    try:
        with urllib.request.urlopen(  # noqa: S310 - fixed loopback health URL
            "http://127.0.0.1:8000/api/v1/health/ready", timeout=3
        ) as response:
            return 0 if response.status == 200 else 1
    except (urllib.error.URLError, TimeoutError):
        return 1


if __name__ == "__main__":
    sys.exit(main())

