"""Skill plugin base + game profiles (keybinds)."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"
SKILL_CLASSES: dict[str, type] = {}


@dataclass
class GameProfile:
    id: str
    name: str
    window_title: str = ""
    keybinds: dict = field(default_factory=dict)

    def key(self, action: str) -> str:
        if action not in self.keybinds:
            raise KeyError(f"No keybind for '{action}' in {self.name}")
        return self.keybinds[action]


def load_profile(game_id: str, overrides: dict | None = None) -> GameProfile:
    data = json.loads((PROFILE_DIR / f"{game_id}.json").read_text(encoding="utf-8"))
    kb = {**data["keybinds"], **(overrides or {})}
    return GameProfile(game_id, data["name"], data.get("window_title", ""), kb)


def register(cls):
    SKILL_CLASSES[cls.name] = cls
    return cls


class Skill:
    """A skill is a named task. `run(ctx, **params)` performs it via ctx.input."""
    name = "base"
    game = "*"           # game id or "*" for all games
    description = ""
    params: dict = {}

    def run(self, ctx, **params) -> str:
        raise NotImplementedError

    # helpers
    @staticmethod
    def tap(ctx, action, n=1, gap=0.15):
        for _ in range(n):
            ctx.input.press(ctx.profile.key(action))
            ctx.input.sleep(gap)

    @staticmethod
    def hold(ctx, action, seconds):
        key = ctx.profile.key(action)
        if key in ("left", "right", "middle"):
            ctx.input.mouse_down(key); ctx.input.sleep(seconds); ctx.input.mouse_up(key)
        else:
            ctx.input.hold(key, seconds)
