"""GameBrain: ties config, safety, input, perception, VLM, skills and addons together."""
from __future__ import annotations
import logging
from .config import Config
from .safety import SafetyGuard, EmergencyStop
from .input_controller import InputController
from .perception import ScreenCapture
from .vlm import VLMAdapter
from .mcp_client import AddonManager
from .skills import SKILL_CLASSES, load_profile

log = logging.getLogger(__name__)
GAMES = ["elden_ring", "dune_awakening", "rocket_league"]


class GameBrain:
    def __init__(self, config: Config | None = None, game: str = "elden_ring", backend=None, capture=None, vlm=None):
        self.config = config or Config.load()
        self.safety = SafetyGuard(self.config.emergency_stop_hotkey)
        self.input = InputController(self.safety, self.config.dry_run, backend)
        self.capture = capture if capture is not None else ScreenCapture(self.config.capture_monitor)
        self.vlm = vlm if vlm is not None else VLMAdapter(self.config.llm)
        self.addons = AddonManager(self.config.mcp_addons)
        self.set_game(game)

    def set_game(self, game: str):
        if game not in GAMES:
            raise ValueError(f"Unknown game {game}; choose {GAMES}")
        self.game = game
        self.profile = load_profile(game, self.config.keybind_overrides.get(game))

    def set_dry_run(self, on: bool):
        self.config.dry_run = self.input.dry_run = on

    def skills(self) -> dict:
        return {n: c for n, c in SKILL_CLASSES.items() if c.game in ("*", self.game)}

    def screenshot_b64(self) -> str:
        return self.capture.to_base64_png(self.capture.grab())

    def run_skill(self, name: str, **params) -> str:
        sk = self.skills().get(name)
        if not sk:
            raise KeyError(f"Skill '{name}' not available for {self.game}")
        self.safety.reset()
        try:
            return sk().run(self, **params)
        except EmergencyStop:
            return "Stopped by emergency stop"

    def tip(self, question: str = "") -> str:
        return self.vlm.tip(self.profile.name, self.screenshot_b64(), question)

    def do(self, goal: str) -> str:
        """Natural-language command -> skill match or VLM-planned action sequence."""
        g = goal.lower()
        for name, cls in self.skills().items():
            if name in g or any(w in g for w in cls.description.lower().split()[:3] if len(w) > 4):
                return self.run_skill(name)
        actions = list(self.profile.keybinds)
        plan = self.vlm.plan_actions(self.profile.name, goal, actions, self.screenshot_b64())
        self.safety.reset()
        try:
            for step in plan:
                key = self.profile.key(step["action"])
                if key in ("left", "right", "middle"):
                    self.input.mouse_down(key); self.input.sleep(step["seconds"]); self.input.mouse_up(key)
                else:
                    self.input.hold(key, step["seconds"])
        except EmergencyStop:
            return "Stopped by emergency stop"
        return f"Executed {len(plan)} planned steps"

    def ask_addon(self, addon: str, tool: str, arguments: dict | None = None) -> str:
        return self.addons.get(addon).call_tool(tool, arguments)
