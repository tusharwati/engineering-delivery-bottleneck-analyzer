import logging
import re
import sys
from typing import Any

# Token redaction patterns
TOKEN_PATTERNS = [
    (re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9+/]+"), "https://hooks.slack.com/services/REDACTED_WEBHOOK"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{16,255}"), "ghp_REDACTED_TOKEN"),
    (re.compile(r"(password|secret|token)=[^&\s]+", re.IGNORECASE), r"\1=REDACTED"),
]


def redact_sensitive(text: str) -> str:
    """Masks secrets, tokens, passwords, and webhook URLs in logs."""
    if not isinstance(text, str):
        return text
    for pattern, replacement in TOKEN_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive credentials from all logged records."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_sensitive(original)


def setup_logger(name: str = "bottleneck_analyzer", level: str = "INFO") -> logging.Logger:
    """Configures and returns a structured redacting logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers if re-called
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()

