"""Record the player's keyboard/mouse input and replay/imitate it.

Recordings are JSON event lists. `PlaystyleModel` builds simple statistics
(key frequencies, hold times, n-gram transitions) to imitate how you play.
"""
from __future__ import annotations
import json, random, time
from collections import Counter, defaultdict
from pathlib import Path


class InputRecorder:
    def __init__(self):
        self.events: list[dict] = []
        self._t0 = None
        self._listeners = []

    def _ts(self):
        return round(time.monotonic() - self._t0, 4)

    def add(self, kind, **data):
        if self._t0 is None:
            self._t0 = time.monotonic()
        self.events.append({"t": self._ts(), "kind": kind, **data})

    def start(self):  # pragma: no cover - needs a display
        from pynput import keyboard, mouse
        self._t0 = time.monotonic()
        k = lambda key: getattr(key, "char", None) or str(key).replace("Key.", "")
        self._listeners = [
            keyboard.Listener(on_press=lambda key: self.add("down", key=k(key)),
                              on_release=lambda key: self.add("up", key=k(key))),
            mouse.Listener(on_click=lambda x, y, b, p: self.add("mdown" if p else "mup", button=b.name, x=x, y=y)),
        ]
        for l in self._listeners:
            l.daemon = True
            l.start()

    def stop(self):
        for l in self._listeners:
            l.stop()
        self._listeners = []

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.events), encoding="utf-8")

    @staticmethod
    def load(path) -> list[dict]:
        return json.loads(Path(path).read_text(encoding="utf-8"))


def replay(events, controller, speed: float = 1.0):
    last = 0.0
    for e in events:
        controller.sleep(max(0.0, (e["t"] - last) / speed))
        last = e["t"]
        if e["kind"] == "down": controller.key_down(e["key"])
        elif e["kind"] == "up": controller.key_up(e["key"])
        elif e["kind"] == "mdown": controller.mouse_down(e.get("button", "left"))
        elif e["kind"] == "mup": controller.mouse_up(e.get("button", "left"))


class PlaystyleModel:
    def __init__(self):
        self.freq = Counter()
        self.hold = defaultdict(list)
        self.trans = defaultdict(Counter)

    def fit(self, events):
        down_at, prev = {}, None
        for e in events:
            if e["kind"] == "down" and e["key"] not in down_at:
                down_at[e["key"]] = e["t"]
                self.freq[e["key"]] += 1
                if prev is not None:
                    self.trans[prev][e["key"]] += 1
                prev = e["key"]
            elif e["kind"] == "up" and e["key"] in down_at:
                self.hold[e["key"]].append(e["t"] - down_at.pop(e["key"]))
        return self

    def avg_hold(self, key) -> float:
        h = self.hold.get(key)
        return sum(h) / len(h) if h else 0.1

    def next_key(self, prev=None, rng=random):
        c = self.trans.get(prev) or self.freq
        if not c:
            return None
        keys, w = zip(*c.items())
        return rng.choices(keys, weights=w)[0]

    def generate(self, n: int, rng=random) -> list[tuple[str, float]]:
        out, prev = [], None
        for _ in range(n):
            k = self.next_key(prev, rng)
            if k is None:
                break
            out.append((k, self.avg_hold(k)))
            prev = k
        return out

    def to_dict(self):
        return {"freq": dict(self.freq), "hold": dict(self.hold), "trans": {k: dict(v) for k, v in self.trans.items()}}

    def summary(self) -> str:
        top = ", ".join(f"{k}({n})" for k, n in self.freq.most_common(8))
        return f"Most used keys: {top or 'none'}"
