import pathlib
import threading
import unittest

from p08 import approval as ap
from p08.approval import ApprovalGate
from p08.mailer import SendBlocked, SimulatedMailer
from p08.store import Store
from tests.helpers import make_app_with, mail

CHAT = 424242


def flow(app, i=1):
    r = app.pipeline.process(mail(i))
    return r, app.store.one("SELECT * FROM approvals WHERE id=?", (r["approval_id"],))


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.app, self.clock = make_app_with()
        self.addCleanup(self.app.stop)

    def cb(self, kind="ap"):
        m = self.app.fake.messages[-1]
        kb = m["reply_markup"]["inline_keyboard"][0]
        return kb[0 if kind == "ap" else 1]["callback_data"]

    def test_sin_clic_cero_envios(self):
        r, _ = flow(self.app)
        self.assertEqual(r["status"], "pendiente_aprobacion")
        self.assertEqual(self.app.store.count_sent(), 0)

    def test_aprobar_envia_una_vez_al_destinatario_original(self):
        flow(self.app)
        self.assertEqual(self.app.gate.decide(self.cb(), CHAT), ap.SENT)
        row = self.app.store.one("SELECT * FROM outbox")
        self.assertEqual(row["recipient"], "cliente1@demo.test")
        self.assertEqual(row["mode"], "simulated")

    def test_doble_clic_secuencial_un_envio(self):
        flow(self.app)
        d = self.cb()
        self.assertEqual(self.app.gate.decide(d, CHAT), ap.SENT)
        self.assertEqual(self.app.gate.decide(d, CHAT), ap.PROCESSED)
        self.assertEqual(self.app.store.count_sent(), 1)

    def test_clics_concurrentes_un_solo_envio(self):
        flow(self.app)
        d, out = self.cb(), []
        ts = [threading.Thread(target=lambda: out.append(self.app.gate.decide(d, CHAT))) for _ in range(20)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(out.count(ap.SENT), 1)
        self.assertEqual(self.app.store.count_sent(), 1)

    def test_otro_chat_rechazado(self):
        flow(self.app)
        self.assertEqual(self.app.gate.decide(self.cb(), 999), ap.DENIED)
        self.assertEqual(self.app.gate.decide(self.cb(), CHAT, user_id=999), ap.DENIED)
        self.assertEqual(self.app.store.count_sent(), 0)
        self.assertEqual(self.app.gate.decide(self.cb(), CHAT), ap.SENT)  # el intento ajeno no quema la aprobacion

    def test_borrador_editado_exige_nueva_aprobacion(self):
        r, _ = flow(self.app)
        old = self.cb()
        new = self.app.gate.edit_draft(r["task_id"], "Hola Ana,\n\nTexto nuevo revisado por una persona.\n\nSaludos")
        self.assertEqual(self.app.gate.decide(old, CHAT), ap.PROCESSED)
        self.assertEqual(self.app.store.count_sent(), 0)
        self.assertEqual(self.app.gate.decide(new.approve_data, CHAT), ap.SENT)
        self.assertIn("Texto nuevo", self.app.store.one("SELECT body FROM outbox")["body"])

    def test_cambio_directo_en_bd_invalida(self):
        r, _ = flow(self.app)
        self.app.store.execute("UPDATE tasks SET draft_body='Cuerpo manipulado' WHERE id=?", (r["task_id"],))
        self.assertEqual(self.app.gate.decide(self.cb(), CHAT), ap.CHANGED)
        self.assertEqual(self.app.store.count_sent(), 0)

    def test_cambio_de_destinatario_invalida(self):
        r, _ = flow(self.app)
        self.app.store.execute("UPDATE tasks SET from_email='evil@attacker.test' WHERE id=?", (r["task_id"],))
        self.assertEqual(self.app.gate.decide(self.cb(), CHAT), ap.CHANGED)
        self.assertEqual(self.app.store.count_sent(), 0)

    def test_expirada(self):
        flow(self.app)
        self.clock.t += 25 * 3600
        self.assertEqual(self.app.gate.decide(self.cb(), CHAT), ap.EXPIRED)
        self.assertEqual(self.app.store.count_sent(), 0)

    def test_firma_falsa_y_ids_ajenos(self):
        r, a = flow(self.app)
        self.assertEqual(self.app.gate.decide(f"ap:{a['id']}:{'0' * 16}", CHAT), ap.BAD_SIG)
        self.assertEqual(self.app.gate.decide(f"ap:{'f' * 12}:{'0' * 16}", CHAT), ap.UNKNOWN)
        self.assertEqual(self.app.gate.decide("basura", CHAT), ap.BAD_SIG)
        self.assertEqual(self.app.gate.decide("ap:" + "x" * 80, CHAT), ap.BAD_SIG)
        sig_rj = self.cb("rj").split(":")[2]
        self.assertEqual(self.app.gate.decide(f"ap:{a['id']}:{sig_rj}", CHAT), ap.BAD_SIG)
        self.assertEqual(self.app.store.count_sent(), 0)

    def test_aprobacion_de_un_borrador_no_sirve_para_otro(self):
        flow(self.app, 1)
        d1 = self.cb()
        _, a2 = flow(self.app, 2)
        self.assertEqual(self.app.gate.decide(f"ap:{a2['id']}:{d1.split(':')[2]}", CHAT), ap.BAD_SIG)
        self.assertEqual(self.app.store.count_sent(), 0)

    def test_rechazar_no_envia(self):
        flow(self.app)
        self.assertEqual(self.app.gate.decide(self.cb("rj"), CHAT), ap.REJECTED)
        self.assertEqual(self.app.gate.decide(self.cb("ap"), CHAT), ap.PROCESSED)
        self.assertEqual(self.app.store.count_sent(), 0)


class NoSendPathTests(unittest.TestCase):
    def test_mailer_sin_prueba_no_entrega(self):
        m = SimulatedMailer(Store())
        with self.assertRaises(SendBlocked):
            m.deliver(object(), "x", "a@b.test", "s", "b")
        m.arm(object())
        with self.assertRaises(SendBlocked):
            m.deliver(object(), "x", "a@b.test", "s", "b")

    def test_modo_real_prohibido(self):
        with self.assertRaises(SendBlocked):
            SimulatedMailer(Store(), mode="smtp")

    def test_cabecera_con_crlf_bloqueada_en_el_mailer(self):
        app, _ = make_app_with()
        self.addCleanup(app.stop)
        with self.assertRaises(SendBlocked):
            app.mailer.deliver(app.gate._proof, "id1", "a@b.test\r\nBcc: x@y.test", "s", "b")
        with self.assertRaises(SendBlocked):
            app.mailer.deliver(app.gate._proof, "id2", "a@b.test", "Hola\r\nBcc: x@y.test", "b")
        self.assertEqual(app.store.count_sent(), 0)

    def test_pipeline_no_tiene_ruta_de_envio(self):
        import p08.pipeline as pl
        app, _ = make_app_with()
        self.addCleanup(app.stop)
        self.assertFalse(any(hasattr(app.pipeline, n) for n in ("send", "deliver", "mailer", "gate")))
        self.assertFalse(hasattr(app.pipeline.requester, "decide"))
        root = pathlib.Path(pl.__file__).parent
        allowed = {"app.py", "approval.py", "mailer.py"}
        for f in root.glob("*.py"):
            if f.name not in allowed:
                src = f.read_text(encoding="utf-8")
                self.assertNotIn("deliver(", src, f.name)
                self.assertNotIn("SimulatedMailer", src, f.name)
                self.assertNotIn("smtplib", src, f.name)

    def test_llave_debil_rechazada(self):
        with self.assertRaises(ValueError):
            ApprovalGate(Store(), b"x", SimulatedMailer(Store()), {1})


if __name__ == "__main__":
    unittest.main()
