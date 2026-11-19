"""ApprovalGate: unico punto del codigo que puede provocar un envio.

Control determinista (no de prompt):
- La aprobacion se ata a sha256(tarea + destinatario + asunto + cuerpo + expiracion).
- callback_data = tipo:id_opaco:firma HMAC; no sirve a otro borrador, otro destinatario ni otro id.
- Un clic = un envio: transicion atomica pending -> used (UPDATE condicional) + UNIQUE(approval_id) en outbox.
- Borrador editado => aprobaciones previas pasan a 'superseded' y hace falta una nueva.
- Solo chat_id y user_id en allowlist.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

from .logsafe import get_logger, opaque
from .mailer import SendBlocked, SimulatedMailer
from .store import Store

log = get_logger("p08.approval")
DEFAULT_TTL = 24 * 3600

# resultados de decide()
SENT = "sent"
REJECTED = "rejected"
DENIED = "denied_chat"
BAD_SIG = "bad_signature"
UNKNOWN = "unknown"
PROCESSED = "already_processed"
EXPIRED = "expired"
CHANGED = "draft_changed"
FAILED = "send_failed"


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    approve_data: str
    reject_data: str
    recipient: str
    subject: str
    body: str
    expires_at: float


def draft_hash(task_id: str, recipient: str, subject: str, body: str, expires_at: float) -> str:
    canon = json.dumps({"t": task_id, "to": recipient, "s": subject, "b": body, "x": int(expires_at)},
                       sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


class ApprovalGate:
    def __init__(self, store: Store, key: bytes, mailer: SimulatedMailer, allowed_chat_ids: set[int],
                 clock=time.time, ttl: int = DEFAULT_TTL):
        if not key or len(key) < 16:
            raise ValueError("clave_de_aprobacion_debil")
        self._store, self._key, self._mailer = store, key, mailer
        self._allowed = frozenset(int(c) for c in allowed_chat_ids)
        self._clock, self._ttl = clock, ttl
        self._proof = object()
        mailer.arm(self._proof)

    # --- firmas ---------------------------------------------------------------
    def _sig(self, kind: str, approval_id: str, h: str) -> str:
        return hmac.new(self._key, f"{kind}:{approval_id}:{h}".encode(), hashlib.sha256).hexdigest()[:16]

    # --- solicitar aprobacion --------------------------------------------------
    def request(self, task_id: str) -> ApprovalRequest:
        t = self._store.one("SELECT * FROM tasks WHERE id=?", (task_id,))
        if t is None or not t["draft_body"]:
            raise ValueError("sin_borrador")
        self._store.execute("UPDATE approvals SET status='superseded' WHERE task_id=? AND status='pending'", (task_id,))
        now = self._clock()
        exp = now + self._ttl
        aid = secrets.token_hex(6)
        h = draft_hash(task_id, t["from_email"], t["draft_subject"], t["draft_body"], exp)
        self._store.execute(
            "INSERT INTO approvals(id,task_id,draft_hash,recipient,expires_at,status,created_at) VALUES(?,?,?,?,?, 'pending', ?)",
            (aid, task_id, h, t["from_email"], exp, now))
        self._store.execute("UPDATE tasks SET status='pendiente_aprobacion' WHERE id=?", (task_id,))
        return ApprovalRequest(aid, f"ap:{aid}:{self._sig('ap', aid, h)}", f"rj:{aid}:{self._sig('rj', aid, h)}",
                               t["from_email"], t["draft_subject"], t["draft_body"], exp)

    def edit_draft(self, task_id: str, new_body: str) -> ApprovalRequest:
        """Editar el borrador invalida toda aprobacion previa; devuelve una solicitud nueva."""
        if not new_body.strip() or len(new_body) > 2000:
            raise ValueError("borrador_invalido")
        self._store.execute("UPDATE approvals SET status='superseded' WHERE task_id=? AND status='pending'", (task_id,))
        self._store.execute("UPDATE tasks SET draft_body=?, draft_version=draft_version+1 WHERE id=?", (new_body, task_id))
        return self.request(task_id)

    # --- decidir ----------------------------------------------------------------
    def decide(self, callback_data: str, chat_id, user_id=None) -> str:
        try:
            cid = int(chat_id)
            uid = int(user_id) if user_id is not None else cid
        except (TypeError, ValueError):
            return DENIED
        if cid not in self._allowed or uid not in self._allowed:
            log.warning("aprobacion_denegada chat=%s", opaque(str(cid)))
            return DENIED
        parts = callback_data.split(":") if isinstance(callback_data, str) and len(callback_data) <= 64 else []
        if len(parts) != 3 or parts[0] not in ("ap", "rj"):
            return BAD_SIG
        kind, aid, sig = parts
        a = self._store.one("SELECT * FROM approvals WHERE id=?", (aid,))
        if a is None:
            return UNKNOWN
        if not hmac.compare_digest(sig, self._sig(kind, aid, a["draft_hash"])):
            return BAD_SIG
        if a["status"] != "pending":
            return PROCESSED
        if self._clock() >= a["expires_at"]:
            self._store.execute("UPDATE approvals SET status='expired' WHERE id=? AND status='pending'", (aid,))
            return EXPIRED
        t = self._store.one("SELECT * FROM tasks WHERE id=?", (a["task_id"],))
        current = draft_hash(a["task_id"], a["recipient"], t["draft_subject"] or "", t["draft_body"] or "", a["expires_at"])
        if t["from_email"] != a["recipient"] or not hmac.compare_digest(current, a["draft_hash"]):
            self._store.execute("UPDATE approvals SET status='invalidated' WHERE id=? AND status='pending'", (aid,))
            log.warning("aprobacion_invalidada_por_cambio task=%s", opaque(a["task_id"]))
            return CHANGED
        # transicion atomica: solo UN llamador gana
        who = str(cid)
        new = "used" if kind == "ap" else "rejected"
        cur = self._store.execute("UPDATE approvals SET status=?, decided_by=? WHERE id=? AND status='pending'", (new, who, aid))
        if cur.rowcount != 1:
            return PROCESSED
        if kind == "rj":
            self._store.execute("UPDATE tasks SET status='descartado' WHERE id=?", (a["task_id"],))
            return REJECTED
        try:
            self._mailer.deliver(self._proof, aid, a["recipient"], t["draft_subject"], t["draft_body"])
        except SendBlocked:
            self._store.execute("UPDATE approvals SET status='send_failed' WHERE id=?", (aid,))
            log.error("envio_bloqueado approval=%s", aid)
            return FAILED
        self._store.execute("UPDATE tasks SET status='enviado' WHERE id=?", (a["task_id"],))
        log.info("enviado approval=%s task=%s", aid, opaque(a["task_id"]))
        return SENT


class Requester:
    """Fachada estrecha que recibe el pipeline: solo puede PEDIR aprobacion, nunca enviar."""

    def __init__(self, gate: ApprovalGate):
        self._request = gate.request

    def request(self, task_id: str) -> ApprovalRequest:
        return self._request(task_id)
