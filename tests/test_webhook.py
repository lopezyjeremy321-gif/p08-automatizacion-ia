import json
import unittest

from p08.app import sign
from tests.helpers import make_app_with, mail, post, signed_headers


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.app, self.clock = make_app_with()
        self.addCleanup(self.app.stop)
        self.port = self.app.serve(block=False)
        self.url = f"http://127.0.0.1:{self.port}/webhook/mail"

    def send(self, payload, headers=None):
        raw = json.dumps(payload).encode()
        h = signed_headers(self.app, raw) if headers is None else headers
        return post(self.url, raw=raw, headers=h)

    def test_sin_firma_401(self):
        code, _ = post(self.url, mail(1), {})
        self.assertEqual(code, 401)
        self.assertEqual(self.app.store.one("SELECT COUNT(*) c FROM tasks")["c"], 0)

    def test_firma_incorrecta_401(self):
        raw = json.dumps(mail(1)).encode()
        h = {"X-P08-Timestamp": str(int(self.clock())), "X-P08-Signature": sign("otro-secreto", str(int(self.clock())), raw)}
        self.assertEqual(post(self.url, raw=raw, headers=h)[0], 401)

    def test_firma_vieja_replay_401(self):
        raw = json.dumps(mail(1)).encode()
        h = signed_headers(self.app, raw, ts=self.clock() - 3600)
        self.assertEqual(post(self.url, raw=raw, headers=h)[0], 401)

    def test_token_n8n_invalido_401_y_valido_200(self):
        self.assertEqual(post(self.url, mail(1), {"X-P08-Token": "mal"})[0], 401)
        self.assertEqual(post(self.url, mail(1), {"X-P08-Token": self.app.cfg.n8n_token})[0], 200)

    def test_firma_valida_200_crea_tarea(self):
        code, out = self.send(mail(1))
        self.assertEqual(code, 200)
        self.assertEqual(out["status"], "pendiente_aprobacion")

    def test_crlf_en_to_y_subject_422_sin_tarea(self):
        for over in ({"from_email": "a@demo.test\r\nBcc: x@y.test"}, {"from_email": "a@demo.test\nBcc: x@y.test"},
                     {"subject": "Hola\r\nBcc: x@y.test"}, {"subject": "Hola\nBcc: x@y.test"}, {"from_name": "Ana\r\nX: y"}):
            code, out = self.send(mail(2, **over))
            self.assertEqual(code, 422, over)
        self.assertEqual(self.app.store.one("SELECT COUNT(*) c FROM tasks")["c"], 0)

    def test_campos_extra_y_tipos_422(self):
        self.assertEqual(self.send({**mail(3), "role": "admin"})[0], 422)
        self.assertEqual(self.send(mail(3, body=5))[0], 422)
        self.assertEqual(self.send(mail(3, body="x" * 30000))[0], 422)

    def test_dedupe_por_message_id(self):
        c1, o1 = self.send(mail(5))
        c2, o2 = self.send(mail(5, subject="otro asunto"))
        self.assertEqual((c1, c2), (200, 200))
        self.assertEqual(o2["status"], "duplicate")
        self.assertEqual(o1["task_id"], o2["task_id"])
        self.assertEqual(self.app.store.one("SELECT COUNT(*) c FROM tasks")["c"], 1)
        self.assertEqual(len(self.app.fake.messages), 1)  # un solo aviso

    def test_cuerpo_gigante_413(self):
        code, _ = post(self.url, raw=b"x" * 100_000, headers={})
        self.assertEqual(code, 413)

    def test_error_generico_sin_stack(self):
        code, out = self.send(mail(9, from_email="no-es-correo"))
        self.assertEqual(code, 422)
        self.assertNotIn("Traceback", json.dumps(out))

    def test_telegram_webhook_sin_secreto_401(self):
        url = f"http://127.0.0.1:{self.port}/telegram/webhook"
        self.assertEqual(post(url, {"update_id": 1}, {})[0], 401)
        self.assertEqual(post(url, {"update_id": 1}, {"X-Telegram-Bot-Api-Secret-Token": "mal"})[0], 401)

    def test_limite_por_hora(self):
        self.app.pipeline.max_inbound = 3
        codes = [self.send(mail(20 + i))[0] for i in range(5)]
        self.assertEqual(codes, [200, 200, 200, 429, 429])


if __name__ == "__main__":
    unittest.main()
