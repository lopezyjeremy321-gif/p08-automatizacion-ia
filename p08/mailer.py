"""Buzon de salida SIMULADO. No existe envio real en este proyecto (guarda de entorno).

El mailer solo entrega si recibe la prueba (`proof`) con la que lo armo el ApprovalGate.
Nadie mas en el codigo tiene esa prueba; el pipeline ni siquiera recibe una referencia al mailer.
"""
from __future__ import annotations

import time

from .errors import P08Error
from .models import EMAIL_RE, has_crlf
from .store import Store


class SendBlocked(P08Error):
    pass


class SimulatedMailer:
    MODE = "simulated"

    def __init__(self, store: Store, mode: str = "simulated", clock=time.time):
        if mode != self.MODE:
            raise SendBlocked("modo_de_envio_no_permitido")  # guarda de entorno: solo pruebas
        self._store, self._clock = store, clock
        self._armed = None

    def arm(self, proof: object) -> None:
        if self._armed is not None:
            raise SendBlocked("ya_armado")
        self._armed = proof

    def deliver(self, proof: object, approval_id: str, recipient: str, subject: str, body: str) -> None:
        if self._armed is None or proof is not self._armed:
            raise SendBlocked("sin_aprobacion")
        # defensa en profundidad: inyeccion de cabeceras
        if has_crlf(recipient) or has_crlf(subject) or not EMAIL_RE.match(recipient):
            raise SendBlocked("cabecera_invalida")
        self._store.execute(
            "INSERT INTO outbox(approval_id,recipient,subject,body,sent_at,mode) VALUES(?,?,?,?,?,?)",
            (approval_id, recipient, subject, body, self._clock(), self.MODE),
        )
