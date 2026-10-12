"""Tkinter desktop GUI."""
from __future__ import annotations
import json, logging, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from .brain import GameBrain, GAMES
from .config import Config, CONFIG_DIR
from .recorder import InputRecorder


class App:
    def __init__(self, root):
        self.root = root
        root.title("Gaming Companion v1.0.0"); root.geometry("760x560")
        self.cfg = Config.load()
        self.brain = GameBrain(self.cfg)
        self.brain.safety.start_hotkey_listener()
        self.recorder = None
        f = ttk.Frame(root, padding=8); f.pack(fill="both", expand=True)

        top = ttk.Frame(f); top.pack(fill="x")
        ttk.Label(top, text="Game:").pack(side="left")
        self.game = tk.StringVar(value=self.brain.game)
        cb = ttk.Combobox(top, textvariable=self.game, values=GAMES, state="readonly", width=18)
        cb.pack(side="left", padx=4); cb.bind("<<ComboboxSelected>>", lambda e: self._set_game())
        self.dry = tk.BooleanVar(value=self.cfg.dry_run)
        ttk.Checkbutton(top, text="Dry-run (no real input)", variable=self.dry,
                        command=lambda: self.brain.set_dry_run(self.dry.get())).pack(side="left", padx=8)
        ttk.Button(top, text=f"STOP ({self.cfg.emergency_stop_hotkey.upper()})",
                   command=self.brain.safety.trigger).pack(side="right")

        mid = ttk.Frame(f); mid.pack(fill="x", pady=6)
        self.skill = tk.StringVar()
        self.skill_cb = ttk.Combobox(mid, textvariable=self.skill, width=28, state="readonly"); self.skill_cb.pack(side="left")
        self.params = ttk.Entry(mid, width=30); self.params.insert(0, "{}"); self.params.pack(side="left", padx=4)
        ttk.Button(mid, text="Run skill (3s delay)", command=self._run_skill).pack(side="left")

        cmd = ttk.Frame(f); cmd.pack(fill="x", pady=4)
        self.cmd = ttk.Entry(cmd); self.cmd.pack(side="left", fill="x", expand=True)
        ttk.Button(cmd, text="Do it", command=self._do).pack(side="left", padx=2)
        ttk.Button(cmd, text="Get tip", command=self._tip).pack(side="left", padx=2)

        rec = ttk.Frame(f); rec.pack(fill="x", pady=4)
        self.rec_btn = ttk.Button(rec, text="Start recording my play", command=self._toggle_rec); self.rec_btn.pack(side="left")
        ttk.Button(rec, text="Settings", command=self._settings).pack(side="right")

        self.log = scrolledtext.ScrolledText(f, height=20); self.log.pack(fill="both", expand=True)
        self._set_game()
        self.say("Ready. Dry-run is ON by default; untick it for real input. Press the stop hotkey anytime.")

    def say(self, msg):
        self.root.after(0, lambda: (self.log.insert("end", msg + "\n"), self.log.see("end")))

    def _bg(self, fn, delay=0):
        def w():
            try:
                if delay: self.say(f"Starting in {delay}s - switch to the game window..."); time.sleep(delay)
                self.say(str(fn()))
            except Exception as e:
                self.say(f"Error: {e}")
        threading.Thread(target=w, daemon=True).start()

    def _set_game(self):
        self.brain.set_game(self.game.get())
        names = list(self.brain.skills()); self.skill_cb["values"] = names
        if names: self.skill.set(names[0])

    def _run_skill(self):
        p = json.loads(self.params.get() or "{}")
        self._bg(lambda: self.brain.run_skill(self.skill.get(), **p), delay=3)

    def _do(self): self._bg(lambda: self.brain.do(self.cmd.get()), delay=3)
    def _tip(self): self._bg(lambda: self.brain.tip(self.cmd.get()))

    def _toggle_rec(self):
        if self.recorder is None:
            self.recorder = InputRecorder(); self.recorder.start()
            self.rec_btn.config(text="Stop recording"); self.say("Recording input...")
        else:
            self.recorder.stop()
            path = CONFIG_DIR / "recordings" / self.brain.game / f"{int(time.time())}.json"
            self.recorder.save(path); self.say(f"Saved {len(self.recorder.events)} events to {path}")
            self.recorder = None; self.rec_btn.config(text="Start recording my play")

    def _settings(self):
        w = tk.Toplevel(self.root); w.title("Settings")
        fields = {"provider": self.cfg.llm.provider, "base_url": self.cfg.llm.base_url,
                  "model": self.cfg.llm.model, "api_key": self.cfg.llm.api_key}
        ents = {}
        for i, (k, v) in enumerate(fields.items()):
            ttk.Label(w, text=k).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            e = ttk.Entry(w, width=50, show="*" if k == "api_key" else ""); e.insert(0, v); e.grid(row=i, column=1); ents[k] = e
        ttk.Label(w, text="MCP addons (JSON)").grid(row=4, column=0, sticky="nw")
        addons = tk.Text(w, width=50, height=6); addons.insert("1.0", json.dumps(self.cfg.mcp_addons, indent=1)); addons.grid(row=4, column=1)
        def save():
            for k, e in ents.items(): setattr(self.cfg.llm, k, e.get())
            self.cfg.mcp_addons = json.loads(addons.get("1.0", "end") or "{}")
            self.say(f"Saved settings to {self.cfg.save()}"); self.brain = GameBrain(self.cfg, self.game.get())
            self.brain.safety.start_hotkey_listener(); w.destroy()
        ttk.Button(w, text="Save", command=save).grid(row=5, column=1, sticky="e", pady=4)


def main():
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk(); App(root); root.mainloop()


if __name__ == "__main__":
    main()
