"""Evaluacion de 50 casos con etiquetas humanas escritas a mano (eval/casos.json).

Uso:  py -3.13 eval/run_eval.py --provider simulado|groq|ollama [--model M] [--drafts]
La clave de Groq se toma de la variable de entorno GROQ_API_KEY (si falta, se lee en memoria del .env del
cerebro; nunca se copia ni se imprime).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from p08.classifier import INCIERTO, LABELS, ClassifierChain, LLMClassifier, SimulatedClassifier  # noqa: E402
from p08.drafter import Drafter  # noqa: E402
from p08.llm import GroqLLM, LLMError, OllamaLLM  # noqa: E402
from p08.models import parse_inbound  # noqa: E402

BRAIN_ENV = pathlib.Path(r"D:\ClaudeBrain\proyectos\viralclip-pro\.env")


def ensure_groq_key() -> None:
    if os.environ.get("GROQ_API_KEY"):
        return
    if BRAIN_ENV.exists():
        for line in BRAIN_ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("GROQ_API_KEY="):
                os.environ["GROQ_API_KEY"] = line.split("=", 1)[1].strip().strip('"')
                return


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="simulado")
    ap.add_argument("--model", default="")
    ap.add_argument("--drafts", action="store_true")
    ap.add_argument("--pause", type=float, default=2.2)
    a = ap.parse_args()
    cases = json.loads((ROOT / "eval" / "casos.json").read_text(encoding="utf-8"))
    assert len(cases) == 50, len(cases)

    llm = None
    if a.provider == "simulado":
        clf, tag, pause = SimulatedClassifier(), "simulado (palabras clave)", 0
    else:
        if a.provider == "groq":
            ensure_groq_key()
            llm = GroqLLM(a.model or "openai/gpt-oss-20b")
            if not llm.available:
                sys.exit("sin GROQ_API_KEY")
        else:
            llm = OllamaLLM(a.model or "llama3.2:3b")
        clf, tag, pause = ClassifierChain([LLMClassifier(llm)]), f"{llm.name}:{llm.model}", a.pause

    rows, drafts_ok = [], []
    for c in cases:
        e = parse_inbound({"message_id": f"<{c['id']}@eval.test>", "from_email": "persona@demo.test", "from_name": "Persona",
                           "subject": c["subject"], "body": c["body"]})
        t0 = time.time()
        r = clf.classify(e)
        lat = time.time() - t0
        row = {"id": c["id"], "grupo": c["grupo"], "gold": c["gold"], "pred": r.label, "conf": round(r.confidence, 2),
               "ok": r.label == c["gold"], "razon": r.reason, "lat_s": round(lat, 2), "asunto": c["subject"][:48]}
        if a.drafts and llm is not None and r.label in ("ventas", "soporte"):
            time.sleep(pause)
            d = Drafter(llm).draft(e, r.label)
            row["borrador"] = d.source
            row["notas_borrador"] = list(d.notes)
        rows.append(row)
        time.sleep(pause)

    n = len(rows)
    ok = sum(r["ok"] for r in rows)
    cols = list(LABELS) + [INCIERTO]
    cm = {g: {p: sum(1 for r in rows if r["gold"] == g and r["pred"] == p) for p in cols} for g in LABELS}
    stats = {}
    for k in LABELS:
        tp = cm[k][k]
        pred_k = sum(cm[g][k] for g in LABELS)
        gold_k = sum(cm[k].values())
        stats[k] = {"precision": tp / pred_k if pred_k else None, "recall": tp / gold_k if gold_k else None, "n": gold_k}
    legit = [r for r in rows if r["gold"] in ("ventas", "soporte")]
    fp_spam = [r["id"] for r in legit if r["pred"] == "spam"]
    answered = [r for r in rows if r["pred"] != INCIERTO]
    lo, hi = wilson(ok, n)
    groups = {}
    for r in rows:
        g = groups.setdefault(r["grupo"], [0, 0])
        g[1] += 1
        g[0] += r["ok"]
    out = {"proveedor": tag, "n": n, "aciertos": ok, "exactitud": ok / n, "ic95": [lo, hi], "semiancho_pts": (hi - lo) / 2 * 100,
           "cobertura": len(answered) / n, "exactitud_respondidos": (sum(r["ok"] for r in answered) / len(answered)) if answered else None,
           "falsos_positivos_spam": fp_spam, "legitimos": len(legit), "fp_spam_tasa": len(fp_spam) / len(legit),
           "matriz": cm, "por_clase": stats, "por_grupo": groups, "filas": rows,
           "lat_media_s": round(sum(r["lat_s"] for r in rows) / n, 2)}
    if a.drafts:
        ds = [r for r in rows if "borrador" in r]
        out["borradores"] = {"total": len(ds), "llm_aceptado": sum(1 for r in ds if r["borrador"] == "llm"),
                             "plantilla_por_rechazo": sum(1 for r in ds if r["borrador"] == "plantilla")}
    slug = (a.provider if not a.model else f"{a.provider}-{a.model}").replace("/", "-")
    (ROOT / "eval").joinpath(f"resultado-{slug}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "docs").joinpath(f"eval-{slug}.md").write_text(render(out), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("proveedor", "aciertos", "exactitud", "semiancho_pts", "cobertura", "falsos_positivos_spam")}, ensure_ascii=False))


def pct(x):
    return "n/d" if x is None else f"{x * 100:.1f} %"


def render(o: dict) -> str:
    cols = list(LABELS) + [INCIERTO]
    L = [f"# Evaluacion P08 - {o['proveedor']}", "",
         f"- Casos: {o['n']} (15 ventas, 15 soporte, 10 spam, 10 dificiles). Etiquetas escritas a mano ANTES de ejecutar el modelo.",
         f"- Aciertos exactos: **{o['aciertos']}/{o['n']} = {pct(o['exactitud'])}** (1 repeticion).",
         f"- Margen: IC 95 % Wilson {pct(o['ic95'][0])} a {pct(o['ic95'][1])} (aprox. +-{o['semiancho_pts']:.0f} pts). Con 50 casos y 1 rep, diferencias menores a ese margen no son concluyentes.",
         f"- Cobertura (no 'incierto'): {pct(o['cobertura'])}; exactitud entre los respondidos: {pct(o['exactitud_respondidos'])}.",
         f"- **Falso positivo de spam** (correo legitimo marcado como spam): {len(o['falsos_positivos_spam'])}/{o['legitimos']} = {pct(o['fp_spam_tasa'])} {o['falsos_positivos_spam'] or ''}",
         f"- Latencia media por clasificacion: {o['lat_media_s']} s", "",
         "## Matriz de confusion (filas = etiqueta humana, columnas = prediccion)", "",
         "| real \\ pred | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for g in LABELS:
        L.append(f"| **{g}** | " + " | ".join(str(o["matriz"][g][p]) for p in cols) + " |")
    L += ["", "## Precision y recall", "", "| clase | n real | precision | recall |", "|---|---|---|---|"]
    for k, s in o["por_clase"].items():
        L.append(f"| {k} | {s['n']} | {pct(s['precision'])} | {pct(s['recall'])} |")
    L += ["", "## Por grupo", "", "| grupo | aciertos |", "|---|---|"]
    for g, (k, n) in o["por_grupo"].items():
        L.append(f"| {g} | {k}/{n} |")
    if "borradores" in o:
        b = o["borradores"]
        L += ["", f"## Borradores (ventas/soporte predichos): {b['total']} generados; aceptados del LLM sin tocar: {b['llm_aceptado']}; plantilla segura por rechazo de validador: {b['plantilla_por_rechazo']}"]
    L += ["", "## Tabla de aciertos por caso", "", "| id | grupo | real | pred | conf | ok | razon | lat s | asunto |", "|---|---|---|---|---|---|---|---|---|"]
    for r in o["filas"]:
        L.append(f"| {r['id']} | {r['grupo']} | {r['gold']} | {r['pred']} | {r['conf']} | {'si' if r['ok'] else 'NO'} | {r['razon']} | {r['lat_s']} | {r['asunto']} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
