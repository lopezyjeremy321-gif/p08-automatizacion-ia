"""Entrada no confiable: validacion estricta (lista cerrada de campos, tamanos, sin CR/LF)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .errors import ValidationError

ALLOWED_KEYS = {"message_id", "from_email", "from_name", "subject", "body", "attachments"}
MAX_BODY = 20_000
MAX_SUBJECT = 200
MAX_NAME = 80
MAX_ATTACHMENTS = 10
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")
MSGID_RE = re.compile(r"^[\w.<>@+=\-:$]{1,200}$")
CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
EXEC_EXT = (".exe", ".bat", ".cmd", ".com", ".scr", ".js", ".vbs", ".ps1", ".msi", ".jar", ".lnk", ".docm", ".xlsm")


@dataclass(frozen=True)
class Email:
    message_id: str
    from_email: str
    from_name: str
    subject: str
    body: str
    attachments: tuple = field(default_factory=tuple)

    @property
    def has_risky_attachment(self) -> bool:
        return any(a.lower().endswith(EXEC_EXT) for a in self.attachments)


def has_crlf(value: str) -> bool:
    return "\r" in value or "\n" in value or "\x00" in value


def parse_inbound(data) -> Email:
    """Valida un dict entrante. Cualquier desvio levanta ValidationError (mensaje generico)."""
    if not isinstance(data, dict):
        raise ValidationError("payload_invalido")
    extra = set(data) - ALLOWED_KEYS
    if extra:
        raise ValidationError("campos_no_permitidos")
    for k in ("message_id", "from_email", "subject", "body"):
        if not isinstance(data.get(k), str):
            raise ValidationError(f"falta_{k}")
    name = data.get("from_name", "")
    if not isinstance(name, str):
        raise ValidationError("from_name_invalido")
    atts = data.get("attachments", [])
    if not isinstance(atts, list) or len(atts) > MAX_ATTACHMENTS or not all(isinstance(a, str) and len(a) <= 120 for a in atts):
        raise ValidationError("attachments_invalido")

    mid, to, subj, body = data["message_id"], data["from_email"], data["subject"], data["body"]
    if not MSGID_RE.match(mid):
        raise ValidationError("message_id_invalido")
    if has_crlf(to) or len(to) > 254 or not EMAIL_RE.match(to):
        raise ValidationError("from_email_invalido")
    if has_crlf(subj) or len(subj) > MAX_SUBJECT:
        raise ValidationError("subject_invalido")
    if has_crlf(name) or len(name) > MAX_NAME:
        raise ValidationError("from_name_invalido")
    if len(body) > MAX_BODY:
        raise ValidationError("body_demasiado_grande")
    body = CTRL_RE.sub("", body)
    return Email(mid, to.lower(), name, subj, body, tuple(atts))
