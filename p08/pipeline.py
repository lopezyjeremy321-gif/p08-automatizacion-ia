"""Flujo: validar -> dedupe -> clasificar -> (borrador) -> tarea -> aviso con boton Aprobar.

Este modulo NO importa ni recibe el mailer: no existe ningun camino de envio aqui.
Lo determinista (fechas, prioridades, enrutado, formato) vive en codigo, no en el LLM.
"""
from __future__ import annotations

import datetime as dt
import re
import secrets
import sqlite3
import time

from .classifier import INCIERTO, detect_injection
from .drafter import Drafter
from .logsafe import get_logger, opaque
from .models import Email, parse_inbound
from .store import Store

log = get_logger("p08.pipeline")
_URGENT = re.compile(r"urgente|caido|ca[ií]da|no puedo (entrar|acceder)|perdi|cobro (doble|duplicado)|bloquead", re.IGNORECASE)
MAX_INBOUND_PER_HOUR = 200


class RateLimited(Exception):
    pass


def priority_for(label: str, email: Email) -> str:
    if label == "spam":
        return "baja"
    if _URGENT.search(f"{email.subject} {email.body}"):
        return "alta"
    return "media"


def due_date_for(label: str, priority: str, today: dt.date) -> str | None:
    days = {"alta": 1, "media": 2 if label == "ventas" else 3}.get(priority)
    due = (today + dt.timedelta(days=days)).isoformat() if days else None
    if due:
        dt.date.fromisoformat(due)  # validado en codigo
    return due


class Pipeline:
    def __init__(self, store: Store, classifier, drafter: Drafter, requester, notifier, clock=time.time,
                 max_inbound_per_hour: int = MAX_INBOUND_PER_HOUR):
        self.store, self.classifier, self.drafter = store, classifier, drafter
        self.requester, self.notifier, self.clock = requester, notifier, clock
        self.max_inbound = max_inbound_per_hour
        self._inbound_hits: list[float] = []

    def _rate_check(self) -> None:
        now = self.clock()
        self._inbound_hits = [t for t in self._inbound_hits if now - t < 3600]
        if len(self._inbound_hits) >= self.max_inbound:
            raise RateLimited()
        self._inbound_hits.append(now)

    def process(self, payload: dict) -> dict:
        email = parse_inbound(payload)  # ValidationError si no cumple el esquema
        dup = self.store.one("SELECT id,status FROM tasks WHERE message_id=?", (email.message_id,))
        if dup:
            log.info("duplicado msg=%s", opaque(email.message_id))
            return {"status": "duplicate", "task_id": dup["id"]}
        self._rate_check()

        res = self.classifier.classify(email)
        injection = detect_injection(email)
        flags = []
        if injection:
            flags.append("posible_inyeccion")
        if email.has_risky_attachment:
            flags.append("adjunto_riesgoso")
        label = res.label
        prio = priority_for(label, email)
        today = dt.datetime.fromtimestamp(self.clock(), dt.timezone.utc).date()
        due = due_date_for(label, prio, today)
        tid = "t_" + secrets.token_hex(5)
        manual = label == INCIERTO or bool(flags)
        status = "spam" if label == "spam" and not flags else "revision_manual" if manual else "nuevo"
        title = f"[{label}] {email.subject[:80]}"
        try:
            self.store.execute(
                "INSERT INTO tasks(id,message_id,from_email,from_name,subject,body,label,confidence,provider,title,priority,due_date,status,flags,created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (tid, email.message_id, email.from_email, email.from_name, email.subject, email.body, label,
                 res.confidence, res.provider, title, prio, due, status, ",".join(flags), self.clock()))
        except sqlite3.IntegrityError:  # carrera con otro hilo: mismo Message-ID
            dup = self.store.one("SELECT id FROM tasks WHERE message_id=?", (email.message_id,))
            return {"status": "duplicate", "task_id": dup["id"]}
        log.info("tarea task=%s label=%s status=%s reason=%s", opaque(tid), label, status, res.reason)

        out = {"status": status, "task_id": tid, "label": label, "confidence": res.confidence, "flags": flags,
               "reason": res.reason}
        if manual:
            self._notify_safe(tid, lambda: self.notifier.notify_manual(tid, label, flags, res.reason))
            return out
        if label == "spam":
            return out

        draft = self.drafter.draft(email, label)
        self.store.execute("UPDATE tasks SET draft_subject=?, draft_body=?, draft_version=1 WHERE id=?",
                           (draft.subject, draft.body, tid))
        req = self.requester.request(tid)
        out.update(status="pendiente_aprobacion", approval_id=req.approval_id, draft_source=draft.source)
        self._notify_safe(tid, lambda: self.notifier.notify_approval(tid, label, req))
        return out

    def _notify_safe(self, tid: str, fn) -> None:
        try:
            fn()
        except Exception:  # el aviso no debe perder la tarea; queda marcada
            self.store.execute("UPDATE tasks SET flags = flags || ',aviso_fallido' WHERE id=?", (tid,))
            log.error("aviso_telegram_fallido")
