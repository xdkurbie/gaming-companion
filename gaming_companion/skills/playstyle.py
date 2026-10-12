from pathlib import Path
from .base import Skill, register
from ..recorder import InputRecorder, PlaystyleModel, replay


@register
class ReplayRecording(Skill):
    name = "replay_recording"; game = "*"
    description = "Replay a recorded input session exactly."
    params = {"path": "recording .json", "speed": "default 1.0"}
    def run(self, ctx, path, speed=1.0, **_):
        ev = InputRecorder.load(path); replay(ev, ctx.input, float(speed))
        return f"Replayed {len(ev)} events"


@register
class ImitatePlaystyle(Skill):
    name = "imitate_playstyle"; game = "*"
    description = "Learn from your recordings and play N key actions in your style."
    params = {"path": "recording .json or folder", "steps": "default 20"}
    def run(self, ctx, path, steps=20, **_):
        p = Path(path); model = PlaystyleModel()
        for f in ([p] if p.is_file() else sorted(p.glob("*.json"))):
            model.fit(InputRecorder.load(f))
        for key, hold in model.generate(int(steps)):
            if key in ("left", "right", "middle"):
                ctx.input.mouse_down(key); ctx.input.sleep(hold); ctx.input.mouse_up(key)
            else:
                ctx.input.hold(key, hold)
        return model.summary()
