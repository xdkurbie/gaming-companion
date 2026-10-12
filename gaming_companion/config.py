"""Configuration loading (JSON in ~/.gaming_companion/config.json + env vars)."""
from __future__ import annotations
import json, os
from dataclasses import dataclass, field, asdict
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("GC_HOME", Path.home() / ".gaming_companion"))
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class LLMConfig:
    provider: str = "openai"  # openai | perplexity | huggingface | local
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    timeout: float = 60.0


@dataclass
class Config:
    dry_run: bool = True
    emergency_stop_hotkey: str = "f12"
    capture_monitor: int = 1
    llm: LLMConfig = field(default_factory=LLMConfig)
    mcp_addons: dict = field(default_factory=dict)  # name -> {"command": [...], "env": {...}}
    keybind_overrides: dict = field(default_factory=dict)  # game -> {action: key}

    def save(self, path: Path | None = None) -> Path:
        path = Path(path or CONFIG_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        path = Path(path or CONFIG_FILE)
        data = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        llm = LLMConfig(**data.pop("llm", {}))
        cfg = cls(llm=llm, **{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        env_key = os.environ.get("GC_API_KEY") or {
            "perplexity": os.environ.get("PERPLEXITY_API_KEY"),
            "huggingface": os.environ.get("HF_TOKEN"),
            "openai": os.environ.get("OPENAI_API_KEY"),
        }.get(cfg.llm.provider)
        if env_key and not cfg.llm.api_key:
            cfg.llm.api_key = env_key
        return cfg
