"""Vision-language model adapter. Speaks the OpenAI-compatible chat API, which
Perplexity, Hugging Face router, OpenAI, Ollama, LM Studio and vLLM all support."""
from __future__ import annotations
import json, re
import requests
from .config import LLMConfig

DEFAULT_URLS = {
    "openai": "https://api.openai.com/v1",
    "perplexity": "https://api.perplexity.ai",
    "huggingface": "https://router.huggingface.co/v1",
    "local": "http://localhost:11434/v1",
}


class VLMAdapter:
    def __init__(self, cfg: LLMConfig, session=None):
        self.cfg = cfg
        self.session = session or requests.Session()

    @property
    def url(self) -> str:
        base = self.cfg.base_url or DEFAULT_URLS.get(self.cfg.provider, DEFAULT_URLS["openai"])
        return base.rstrip("/") + "/chat/completions"

    def chat(self, prompt: str, image_b64: str | None = None, system: str | None = None) -> str:
        content = [{"type": "text", "text": prompt}]
        if image_b64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}})
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content if image_b64 else prompt})
        headers = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            headers["Authorization"] = f"Bearer {self.cfg.api_key}"
        r = self.session.post(self.url, headers=headers, timeout=self.cfg.timeout,
                              json={"model": self.cfg.model, "messages": messages})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def tip(self, game: str, image_b64: str | None, question: str = "") -> str:
        return self.chat(question or "What should I do next? Give short, concrete tips.", image_b64,
                         system=f"You are an expert {game} coach looking at the player's screen.")

    def plan_actions(self, game: str, goal: str, actions: list[str], image_b64: str | None) -> list[dict]:
        """Ask the model for a JSON list of steps using only known action names."""
        prompt = (f"Goal: {goal}\nAllowed actions: {', '.join(actions)}\n"
                  'Reply ONLY with JSON: [{"action": name, "seconds": float}] (max 20 steps).')
        text = self.chat(prompt, image_b64, system=f"You control a {game} player character.")
        return parse_plan(text, actions)


def parse_plan(text: str, allowed: list[str]) -> list[dict]:
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        steps = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for s in steps[:20]:
        if isinstance(s, dict) and s.get("action") in allowed:
            out.append({"action": s["action"], "seconds": max(0.0, min(float(s.get("seconds", 0.1)), 10.0))})
    return out
