import logging

from app.core.logging import configure_logging


def test_http_client_logs_are_suppressed_to_protect_tokens() -> None:
    configure_logging("INFO")
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
