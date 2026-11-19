"""Adaptador OPCIONAL a Supabase (PostgREST) para tareas, aprobaciones y dedupe. Sin probar contra la nube.

Usa solo URL + clave publishable + JWT de usuario (RLS decide). Nunca la service_role.
"""
from __future__ import annotations

import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

ENV_FILE = pathlib.Path(r"D:\ClaudeBrain\proyectos\_supabase\proyecto-A.env")


def load_settings(env_file: pathlib.Path = ENV_FILE) -> tuple[str, str]:
    vals = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    url = os.environ.get("SUPABASE_URL") or vals.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY") or vals.get("SUPABASE_PUBLISHABLE_KEY", "")
    return url.rstrip("/"), key


class SupabaseStore:
    def __init__(self, url: str, publishable_key: str, user_jwt: str):
        if not (url and publishable_key and user_jwt):
            raise ValueError("faltan_url_clave_o_jwt")
        self._url, self._h = url, {"apikey": publishable_key, "Authorization": f"Bearer {user_jwt}",
                                   "Content-Type": "application/json"}

    def _req(self, method: str, path: str, body=None, prefer: str = "return=representation"):
        req = urllib.request.Request(f"{self._url}/rest/v1/{path}", method=method, headers={**self._h, "Prefer": prefer},
                                     data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
        return json.loads(raw) if raw else []

    def insert_task_dedupe(self, row: dict) -> bool:
        """True si es nuevo; False si el Message-ID ya existia (unique owner_id+message_id)."""
        out = self._req("POST", "p08_tasks?on_conflict=owner_id,message_id", row,
                        "resolution=ignore-duplicates,return=representation")
        return bool(out)

    def insert_approval(self, row: dict) -> None:
        self._req("POST", "p08_approvals", row)

    def claim_approval(self, approval_id: str, decided_by: str, new_status: str = "used") -> bool:
        """Transicion atomica pending -> used/rejected: solo un llamador obtiene la fila."""
        q = f"p08_approvals?id=eq.{urllib.parse.quote(approval_id)}&status=eq.pending"
        return len(self._req("PATCH", q, {"status": new_status, "decided_by": decided_by})) == 1

    def record_outbox(self, approval_id: str, recipient: str, subject: str, body: str) -> None:
        self._req("POST", "p08_outbox", {"approval_id": approval_id, "recipient": recipient, "subject": subject,
                                         "body": body, "mode": "simulated"})
