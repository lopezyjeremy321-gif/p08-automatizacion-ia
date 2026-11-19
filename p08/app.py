"""Servidor HTTP (stdlib) y raiz de composicion. Unico modulo que junta mailer + gate + pipeline."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import approval as ap
from .approval import ApprovalGate, Requester
from .classifier import ClassifierChain, LLMClassifier, SimulatedClassifier
from .drafter import Drafter
from .errors import ValidationError
from .llm import GroqLLM, OllamaLLM
from .logsafe import get_logger
from .mailer import SimulatedMailer
from .pipeline import Pipeline, RateLimited
from .store import Store
from .telegram import FakeTelegram, Notifier, TelegramClient, REAL_API, extract_callback

log = get_logger("p08.app")
MAX_REQUEST = 64 * 1024
TS_WINDOW = 300
ANSWERS = {
    ap.SENT: "Enviado (buzon simulado).", ap.REJECTED: "Borrador rechazado. No se envio nada.",
    ap.DENIED: "Este chat no esta autorizado.", ap.BAD_SIG: "Aprobacion invalida.",
    ap.UNKNOWN: "Aprobacion desconocida.", ap.PROCESSED: "Esta aprobacion ya se uso o fue reemplazada.",
    ap.EXPIRED: "La aprobacion caduco. Pide una nueva.", ap.CHANGED: "El borrador cambio. Hace falta una nueva aprobacion.",
    ap.FAILED: "El envio fue bloqueado por seguridad.",
}


def sign(secret: str, ts: str, raw: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), ts.encode() + b"." + raw, hashlib.sha256).hexdigest()


@dataclass
class Config:
    port: int = 3180
    db_path: str = ":memory:"
    webhook_secret: str = field(default_factory=lambda: secrets.token_hex(16))
    n8n_token: str = field(default_factory=lambda: secrets.token_hex(16))
    approval_key: str = field(default_factory=lambda: secrets.token_hex(16))
    telegram_secret: str = field(default_factory=lambda: secrets.token_hex(16))
    telegram_token: str = ""          # vacio = modo simulado
    telegram_api: str = REAL_API
    sim_port: int = 3183
    allowed_chat_ids: tuple = (424242,)
    llm_mode: str = "simulado"        # simulado | groq | auto
    send_mode: str = "simulated"

    @classmethod
    def from_env(cls) -> "Config":
        e = os.environ
        d = cls()
        ids = tuple(int(x) for x in e.get("P08_ALLOWED_CHAT_IDS", "").split(",") if x.strip()) or d.allowed_chat_ids
        return cls(port=int(e.get("P08_PORT", d.port)), db_path=e.get("P08_DB", d.db_path),
                   webhook_secret=e.get("P08_WEBHOOK_SECRET") or d.webhook_secret, n8n_token=e.get("P08_N8N_TOKEN") or d.n8n_token,
                   approval_key=e.get("P08_APPROVAL_KEY") or d.approval_key, telegram_secret=e.get("P08_TELEGRAM_SECRET") or d.telegram_secret,
                   telegram_token=e.get("P08_TELEGRAM_BOT_TOKEN", ""), sim_port=int(e.get("P08_SIM_PORT", d.sim_port)),
                   allowed_chat_ids=ids, llm_mode=e.get("P08_LLM", "simulado"), send_mode=e.get("P08_SEND_MODE", "simulated"))


class App:
    def __init__(self, cfg: Config, classifier=None, drafter=None, clock=time.time):
        self.cfg, self.clock = cfg, clock
        self.store = Store(cfg.db_path)
        self.simulated_tg = not cfg.telegram_token
        self.fake: FakeTelegram | None = None
        if self.simulated_tg:
            self.fake = FakeTelegram(cfg.sim_port)
            self.fake.start()
            base, token = f"http://127.0.0.1:{self.fake.port}", "sim"
        else:
            base, token = cfg.telegram_api, cfg.telegram_token
        self.notifier = Notifier(TelegramClient(token, base), next(iter(cfg.allowed_chat_ids)), self.simulated_tg)
        self.mailer = SimulatedMailer(self.store, cfg.send_mode, clock)
        self.gate = ApprovalGate(self.store, cfg.approval_key.encode(), self.mailer, set(cfg.allowed_chat_ids), clock)
        cls, drf = self._build_llm_parts(cfg)
        self.pipeline = Pipeline(self.store, classifier or cls, drafter or drf, Requester(self.gate), self.notifier, clock)
        self._hits: dict[str, list[float]] = {}
        self._httpd: ThreadingHTTPServer | None = None

    @staticmethod
    def _build_llm_parts(cfg: Config):
        if cfg.llm_mode == "simulado":
            return SimulatedClassifier(), Drafter(None)
        providers, writer = [], None
        groq = GroqLLM()
        if cfg.llm_mode in ("groq", "auto") and groq.available:
            providers.append(LLMClassifier(groq))
            writer = groq
        ollama = OllamaLLM()
        if cfg.llm_mode == "auto" and ollama.available:
            providers.append(LLMClassifier(ollama))
            writer = writer or ollama
        if not providers:
            return SimulatedClassifier(), Drafter(None)
        return ClassifierChain(providers), Drafter(writer)

    # ------------------------------------------------------------------ auth
    def authorized(self, headers, raw: bytes) -> bool:
        tok = headers.get("X-P08-Token")
        if tok and hmac.compare_digest(tok, self.cfg.n8n_token):
            return True
        sig, ts = headers.get("X-P08-Signature"), headers.get("X-P08-Timestamp")
        if not sig or not ts:
            return False
        try:
            if abs(self.clock() - float(ts)) > TS_WINDOW:
                return False
        except ValueError:
            return False
        return hmac.compare_digest(sig, sign(self.cfg.webhook_secret, ts, raw))

    def _ip_limited(self, ip: str, per_min: int = 120) -> bool:
        now = self.clock()
        hits = [t for t in self._hits.get(ip, []) if now - t < 60]
        hits.append(now)
        self._hits[ip] = hits
        return len(hits) > per_min

    # --------------------------------------------------------------- handlers
    def handle_mail(self, headers, raw: bytes) -> tuple[int, dict]:
        if not self.authorized(headers, raw):
            return 401, {"error": "no_autorizado"}
        try:
            payload = json.loads(raw or b"{}")
            return 200, self.pipeline.process(payload)
        except (ValueError, ValidationError) as e:
            return 422, {"error": getattr(e, "args", ["payload_invalido"])[0] if isinstance(e, ValidationError) else "json_invalido"}
        except RateLimited:
            return 429, {"error": "limite_por_hora"}
        except Exception:
            log.error("error_interno_mail")
            return 500, {"error": "error_interno"}

    def handle_telegram(self, headers, raw: bytes) -> tuple[int, dict]:
        got = headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(got, self.cfg.telegram_secret):
            return 401, {"error": "no_autorizado"}
        try:
            cb = extract_callback(json.loads(raw or b"{}"))
        except ValueError:
            cb = None
        if cb is None:
            return 200, {"ignored": True}
        cb_id, data, chat_id, user_id = cb
        code = self.gate.decide(data, chat_id, user_id)
        answer = ANSWERS.get(code, "No se pudo procesar.")
        self.notifier.answer(cb_id, answer)
        return 200, {"result": code, "answer": answer}

    def handle_edit(self, headers, raw: bytes, task_id: str) -> tuple[int, dict]:
        if not self.authorized(headers, raw):
            return 401, {"error": "no_autorizado"}
        try:
            body = json.loads(raw)["body"]
            req = self.gate.edit_draft(task_id, body)
            self.notifier.notify_approval(task_id, "editado", req)
            return 200, {"status": "pendiente_aprobacion", "approval_id": req.approval_id}
        except (ValueError, KeyError, TypeError):
            return 422, {"error": "borrador_invalido"}

    # ----------------------------------------------------------------- server
    def serve(self, block: bool = True) -> int:
        app = self

        class H(BaseHTTPRequestHandler):
            server_version = "p08"
            sys_version = ""

            def log_message(self, *a):
                pass

            def _send(self, code: int, obj, ctype="application/json"):
                b = obj.encode() if isinstance(obj, str) else json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(b)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(b)

            def _read(self):
                n = int(self.headers.get("Content-Length") or 0)
                if n > MAX_REQUEST:
                    return None
                return self.rfile.read(n)

            def do_GET(self):
                if self.path == "/healthz":
                    return self._send(200, {"ok": True, "telegram": "simulado" if app.simulated_tg else "real"})
                if self.path == "/tasks.csv" and app.authorized(self.headers, b""):
                    return self._send(200, app.store.export_csv(), "text/csv; charset=utf-8")
                self._send(404, {"error": "no_encontrado"})

            def do_POST(self):
                if app._ip_limited(self.client_address[0]):
                    return self._send(429, {"error": "demasiadas_peticiones"})
                raw = self._read()
                if raw is None:
                    return self._send(413, {"error": "demasiado_grande"})
                if self.path == "/webhook/mail":
                    return self._send(*app.handle_mail(self.headers, raw))
                if self.path == "/telegram/webhook":
                    return self._send(*app.handle_telegram(self.headers, raw))
                if self.path.startswith("/api/tasks/") and self.path.endswith("/draft"):
                    tid = self.path.split("/")[3]
                    return self._send(*app.handle_edit(self.headers, raw, tid))
                self._send(404, {"error": "no_encontrado"})

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.cfg.port), H)
        port = self._httpd.server_address[1]
        if self.fake is not None:
            self.fake.webhook_url = f"http://127.0.0.1:{port}/telegram/webhook"
            self.fake.webhook_secret = self.cfg.telegram_secret
        if block:
            self._httpd.serve_forever()
        else:
            threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        return port

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self.fake:
            self.fake.stop()


def main() -> None:
    cfg = Config.from_env()
    app = App(cfg)
    log.info("p08 escuchando puerto=%s telegram=%s llm=%s", cfg.port, "simulado" if app.simulated_tg else "real", cfg.llm_mode)
    if os.environ.get("P08_PRINT_SECRETS") == "1":  # solo desarrollo local, para scripts de demo
        print(json.dumps({"webhook_secret": cfg.webhook_secret, "n8n_token": cfg.n8n_token}), flush=True)
    app.serve(block=True)


if __name__ == "__main__":
    main()
