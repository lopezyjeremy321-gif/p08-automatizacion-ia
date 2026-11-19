"""Control programatico de 'tics de IA' en los borradores (espanol).

Aplica de forma verificable las reglas del skill /humanizer (blader, MIT): contraste 'no solo X sino Y',
cierres de una linea, aperturas teatrales, rayas largas, negritas/markdown, frases vacias.
El LLM recibe las reglas en el prompt; este modulo las comprueba despues, porque un prompt no es un control.
"""
from __future__ import annotations

import re

HUMANIZER_RULES = (
    "Escribe como una persona del equipo, no como un asistente. Evita: 'no solo X, sino Y' y 'no es X, es Y'; "
    "frases de relleno como 'espero que este mensaje te encuentre bien', 'no dude en contactarnos', 'es importante destacar'; "
    "aperturas teatrales; cierres de una sola linea que repiten lo dicho; rayas largas; negritas, listas y markdown; "
    "mas de un signo de exclamacion; adjetivos inflados ('excelente', 'increible'). Frases de longitud variada, concretas."
)

_TELLS = {
    "contraste_no_x_sino_y": r"\bno\s+(es\s+)?(solo|solamente|s[oó]lo|simplemente)\b.{0,80}\b(sino|es)\b|\bno\s+es\b[^.]{0,60},\s*es\b",
    "relleno_cortesia": r"espero que (este|esta|te|le|se encuentre)|no (dude|dudes|duden) en|quedo a su entera disposici[oó]n|esperamos haber resuelto",
    "frase_vacia": r"es importante (destacar|se[nñ]alar)|cabe (destacar|mencionar)|sin lugar a dudas|en el (panorama|mundo) actual|hoy en d[ií]a",
    "resto_de_chat": r"aqu[ií] tienes|como (modelo|asistente|ia)\b|claro,? (aqu[ií]|por supuesto)|\bborrador\b:",
    "raya_larga": "—",
    "markdown": r"\*\*|^#{1,6}\s|^\s*[-*]\s+\S|`",
    "exclamaciones": r"!.*!",
    "adjetivo_inflado": r"\b(excelente|incre[ií]ble|extraordinari[oa]|revolucionari[oa]|inigualable)\b",
}
_TELLS_RE = {k: re.compile(v, re.IGNORECASE | re.MULTILINE | re.DOTALL) for k, v in _TELLS.items()}


def lint(text: str) -> list[str]:
    return [name for name, rx in _TELLS_RE.items() if rx.search(text)]


def clean(text: str) -> str:
    """Limpieza determinista de lo que se puede arreglar sin cambiar el sentido."""
    text = text.replace("—", ", ").replace("–", "-")
    text = re.sub(r"\*\*|`", "", text)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"!+", ".", text)
    text = re.sub(r"\s+,", ",", text)
    return re.sub(r"[ \t]+", " ", text).strip()
