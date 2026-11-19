"""Clientes LLM gratis: Groq (clave por variable de entorno) y Ollama (respaldo local)."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


class LLMError(Exception):
    pass


def _post(url: str, payload: dict, headers: dict, timeout: float, retries: int, sleep=time.sleep) -> dict:
    data = json.dumps(payload).encode()
    last = "desconocido"
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "p08-correo-a-tareas/0.1", **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f"http_{e.code}"
            if e.code not in (429, 500, 502, 503, 504):
                break
            ra = e.headers.get("Retry-After") if e.headers else None
            try:
                wait = min(float(ra), 20) if ra else 2 ** attempt
            except ValueError:
                wait = 2 ** attempt
            sleep(wait)
        except (urllib.error.URLError, TimeoutError, OSError):
            last = "red"
            sleep(2 ** attempt)
    raise LLMError(last)


class GroqLLM:
    name = "groq"

    def __init__(self, model: str = "openai/gpt-oss-20b", api_key: str | None = None, sleep=time.sleep):
        self.model = model
        self._key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY", "")
        self._sleep = sleep

    @property
    def available(self) -> bool:
        return bool(self._key)

    def complete(self, system: str, user: str, json_mode: bool = False, max_tokens: int = 400) -> str:
        if not self._key:
            raise LLMError("sin_clave")
        payload = {"model": self.model, "temperature": 0, "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if self.model.startswith("openai/gpt-oss"):
            payload["reasoning_effort"] = "low"
            payload["max_tokens"] = max(max_tokens, 200 if json_mode else 450)  # el razonamiento consume tokens
        out = _post(GROQ_URL, payload, {"Authorization": f"Bearer {self._key}"}, 30, 3, self._sleep)
        try:
            return out["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise LLMError("respuesta_invalida")


class OllamaLLM:
    name = "ollama"

    def __init__(self, model: str = "llama3.2:3b", url: str = OLLAMA_URL):
        self.model, self.url = model, url

    @property
    def available(self) -> bool:
        try:
            with urllib.request.urlopen(self.url.replace("/api/chat", "/api/tags"), timeout=2) as r:
                names = [m["name"] for m in json.loads(r.read()).get("models", [])]
            return self.model in names
        except Exception:
            return False

    def complete(self, system: str, user: str, json_mode: bool = False, max_tokens: int = 400) -> str:
        payload = {"model": self.model, "stream": False, "options": {"temperature": 0, "num_predict": max_tokens},
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if json_mode:
            payload["format"] = "json"
        out = _post(self.url, payload, {}, 120, 1)
        try:
            return out["message"]["content"]
        except (KeyError, TypeError):
            raise LLMError("respuesta_invalida")
