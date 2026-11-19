"""Adaptador Telegram (Bot API) + servidor Telegram SIMULADO para pruebas locales.

Token vacio => modo simulado: el cliente apunta al servidor falso en 127.0.0.1 y nada sale a internet.
No se usa ni se toca el bot de ViralClip. El token real (bot nuevo con @BotFather) lo crea Luis.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .logsafe import get_logger

log = get_logger("p08.telegram")
REAL_API = "https://api.telegram.org"


class TelegramClient:
    def __init__(self, token: str, base_url: str):
        self._token, self._base = token, base_url.rstrip("/")

    def call(self, method: str, payload: dict) -> dict:
        req = urllib.request.Request(f"{self._base}/bot{self._token}/{method}", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())


class Notifier:
    def __init__(self, client: TelegramClient, chat_id: int, simulated: bool):
        self.client, self.chat_id, self.simulated = client, chat_id, simulated

    def notify_approval(self, task_id: str, label: str, req) -> None:
        tag = "SIMULADO - " if self.simulated else ""
        text = (f"{tag}Borrador pendiente de aprobacion\nTarea: {task_id} ({label})\n"
                f"Para: {req.recipient}\nAsunto: {req.subject}\n\n{req.body}\n\n"
                "No se envia nada hasta que pulses Aprobar.")
        self.client.call("sendMessage", {"chat_id": self.chat_id, "text": text, "reply_markup": {"inline_keyboard": [[
            {"text": "Aprobar y enviar", "callback_data": req.approve_data},
            {"text": "Rechazar", "callback_data": req.reject_data}]]}})

    def notify_manual(self, task_id: str, label: str, flags: list, reason: str) -> None:
        motivo = ", ".join(flags) if flags else reason
        self.client.call("sendMessage", {"chat_id": self.chat_id, "text":
                         f"Revision manual\nTarea: {task_id} (etiqueta: {label})\nMotivo: {motivo}\nSin borrador y sin boton de envio."})

    def answer(self, callback_id: str, text: str) -> None:
        try:
            self.client.call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})
        except Exception:
            log.error("answer_callback_fallido")


def extract_callback(update: dict):
    """(callback_id, data, chat_id, user_id) o None si la actualizacion no es un clic valido."""
    cq = update.get("callback_query") if isinstance(update, dict) else None
    if not isinstance(cq, dict):
        return None
    try:
        return str(cq["id"]), str(cq["data"]), cq["message"]["chat"]["id"], cq["from"]["id"]
    except (KeyError, TypeError):
        return None


# ------------------------------- servidor simulado ------------------------------------
_PAGE = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Telegram simulado</title><style>
:root{--bg:#f3f1ec;--ink:#1d2330;--mute:#5a6372;--card:#fff;--line:#d9d5cb;--accent:#1f5f8b;--accent-ink:#fff;--bad:#8a2d2d;--ok:#1d6b4a}
@media (prefers-color-scheme:dark){:root{--bg:#161a22;--ink:#e8e6e0;--mute:#9aa3b2;--card:#202634;--line:#323a4b;--accent:#6fb1de;--accent-ink:#0e1520;--bad:#e49a9a;--ok:#7fd0a8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,"Segoe UI",sans-serif}
main{max-width:640px;margin:0 auto;padding:24px 16px 64px}h1{font-size:1.25rem;margin:0 0 4px}
.sub{color:var(--mute);margin:0 0 20px;font-size:.9rem}
.msg{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:0 0 14px}
.msg pre{white-space:pre-wrap;word-break:break-word;font:inherit;margin:0 0 10px}
.btns{display:flex;gap:8px;flex-wrap:wrap}
button{min-height:44px;padding:0 16px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:var(--accent-ink);font:inherit;font-weight:600;cursor:pointer}
button.sec{background:transparent;color:var(--ink);border-color:var(--line)}
button:focus-visible{outline:2px solid var(--ink);outline-offset:2px}button[disabled]{opacity:.5;cursor:default}
.res{margin-top:8px;font-size:.9rem;color:var(--mute)}.empty{color:var(--mute);border:1px dashed var(--line);border-radius:10px;padding:20px}
@media (prefers-reduced-motion:no-preference){.msg{animation:in .2s ease-out}@keyframes in{from{opacity:0;transform:translateY(4px)}}}
</style></head><body><main><h1>Chat de aprobacion (Telegram simulado)</h1>
<p class="sub">Servidor falso local. Nada sale a internet. Cada boton envia el mismo callback firmado que enviaria Telegram.</p>
<div id="list" aria-live="polite"></div></main><script>
const list=document.getElementById('list');
async function load(){const r=await fetch('/__sim/messages');const m=await r.json();
 if(!m.length){list.innerHTML='<p class="empty">Sin mensajes. Envia un correo de prueba al flujo para ver el aviso aqui.</p>';return}
 list.innerHTML='';for(const x of m){const d=document.createElement('div');d.className='msg';
  const p=document.createElement('pre');p.textContent=x.text;d.appendChild(p);
  const kb=(x.reply_markup&&x.reply_markup.inline_keyboard||[]).flat();
  if(kb.length){const b=document.createElement('div');b.className='btns';
   kb.forEach((k,i)=>{const e=document.createElement('button');e.textContent=k.text;if(i)e.className='sec';
    e.onclick=async()=>{const r=await fetch('/__sim/click',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message_id:x.message_id,data:k.callback_data})});
     const j=await r.json();res.textContent='Resultado: '+(j.answer||j.error||'sin respuesta');};b.appendChild(e)});
   d.appendChild(b);var res=document.createElement('div');res.className='res';res.setAttribute('role','status');d.appendChild(res)}
  list.appendChild(d)}}
load();setInterval(load,4000);
</script></body></html>"""


class FakeTelegram:
    """Imita lo minimo de la Bot API y permite 'pulsar' botones (POST al webhook de la app con su secreto)."""

    def __init__(self, port: int, webhook_url: str = "", webhook_secret: str = ""):
        self.port, self.webhook_url, self.webhook_secret = port, webhook_url, webhook_secret
        self.messages: list[dict] = []
        self.answers: list[dict] = []
        self._lock = threading.Lock()
        self._httpd: ThreadingHTTPServer | None = None
        self._update_id = 1000

    def click(self, message_id: int, data: str, chat_id=None, user_id=None) -> dict:
        with self._lock:
            msg = next((m for m in self.messages if m["message_id"] == message_id), None)
            self._update_id += 1
            uid = self._update_id
        cid = chat_id if chat_id is not None else (msg["chat_id"] if msg else 0)
        update = {"update_id": uid, "callback_query": {"id": f"cb{uid}", "from": {"id": user_id if user_id is not None else cid},
                                                        "message": {"message_id": message_id, "chat": {"id": cid}}, "data": data}}
        req = urllib.request.Request(self.webhook_url, data=json.dumps(update).encode(), headers={
            "Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": self.webhook_secret})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return {"error": f"http_{e.code}"}

    def start(self) -> None:
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, obj, code=200):
                b = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def _body(self):
                n = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(min(n, 1_000_000)) or b"{}")

            def do_GET(self):
                if self.path == "/__sim/messages":
                    with outer._lock:
                        return self._json(list(outer.messages))
                if self.path == "/":
                    b = _PAGE.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(b)))
                    self.end_headers()
                    return self.wfile.write(b)
                self._json({"ok": False}, 404)

            def do_POST(self):
                data = self._body()
                if self.path.startswith("/bot") and self.path.count("/") == 2:
                    method = self.path.rsplit("/", 1)[1]
                    with outer._lock:
                        if method == "sendMessage":
                            mid = len(outer.messages) + 1
                            outer.messages.append({"message_id": mid, "chat_id": data.get("chat_id"), "text": data.get("text", ""),
                                                   "reply_markup": data.get("reply_markup")})
                            return self._json({"ok": True, "result": {"message_id": mid}})
                        if method == "answerCallbackQuery":
                            outer.answers.append(data)
                            return self._json({"ok": True, "result": True})
                    return self._json({"ok": False}, 404)
                if self.path == "/__sim/click":
                    r = outer.click(int(data.get("message_id", 0)), str(data.get("data", "")), data.get("chat_id"), data.get("user_id"))
                    return self._json(r)
                self._json({"ok": False}, 404)

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.port), H)
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        if self.port == 0:
            self.port = self._httpd.server_address[1]

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
