"""
Centralized logging for the API test framework.

Every request/response and assertion result is logged to both the console
(INFO level) and a log file under reports/ (DEBUG level) so failures can be
diagnosed after a CI run using only the uploaded report artifact.
"""
import logging
import os

_LOG_FILE = os.environ.get("API_FRAMEWORK_LOG_FILE", "reports/test_run.log")
_LOGGER_NAME = "api_framework"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)

    if logger.handlers:
        # Already configured (avoid duplicate handlers on repeated imports)
        return logger

    logger.setLevel(logging.DEBUG)

    log_dir = os.path.dirname(_LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
