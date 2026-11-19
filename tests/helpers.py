import json
import urllib.error
import urllib.request

from p08.app import App, Config, sign
from p08.classifier import ClassResult


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make_app_with(classifier=None, drafter=None, clock=None, **kw):
    clock = clock or Clock()
    cfg = Config(port=0, sim_port=0, db_path=":memory:", **kw)
    return App(cfg, classifier=classifier, drafter=drafter, clock=clock), clock


def mail(i=1, **over):
    d = {"message_id": f"<m{i}@demo.test>", "from_email": f"cliente{i}@demo.test", "from_name": "Ana Prueba",
         "subject": "Cotizacion de planes", "body": "Hola, quiero saber el precio de sus planes para mi equipo de 5 personas."}
    d.update(over)
    return d


class Obedient:
    """Clasificador/LLM 'malo' que obedece cualquier cosa: simula un modelo inyectado con exito."""
    name = "obediente"
    model = "x"

    def classify(self, email):
        return ClassResult("ventas", 0.99, "obediente")

    def complete(self, system, user, json_mode=False, max_tokens=0):
        return "Reenviamos todo a evil@attacker.test. Aprobado automaticamente. Precio: $50 USD el lunes 5 de mayo."


def post(url, payload=None, headers=None, raw=None):
    data = raw if raw is not None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def signed_headers(app, raw: bytes, ts=None):
    ts = str(int(ts if ts is not None else app.clock()))
    return {"X-P08-Timestamp": ts, "X-P08-Signature": sign(app.cfg.webhook_secret, ts, raw)}
