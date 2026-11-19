"""Logs sin PII: solo ids opacos, etiquetas y estados. El filtro es una red de seguridad."""
from __future__ import annotations

import hashlib
import logging
import re

_EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+(\.[\w\-]+)+")
_PHONE = re.compile(r"\+?\d[\d\s().\-]{7,}\d")
_TOKEN = re.compile(r"\b(?:ap|rj):[0-9a-f]{12}:[0-9a-f]{16}\b")


def opaque(value: str) -> str:
    """Identificador corto no reversible para correlacionar eventos sin exponer datos."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]


def scrub(text: str) -> str:
    text = _EMAIL.sub("[email]", text)
    text = _TOKEN.sub("[token]", text)
    return _PHONE.sub("[tel]", text)


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub(str(record.getMessage()))
        record.args = ()
        return True


def get_logger(name: str = "p08") -> logging.Logger:
    log = logging.getLogger(name)
    if not any(isinstance(f, RedactFilter) for f in log.filters):
        log.addFilter(RedactFilter())
    return log
