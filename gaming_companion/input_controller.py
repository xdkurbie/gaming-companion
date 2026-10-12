"""Keyboard/mouse output via pydirectinput (DirectInput scan codes, works in games).

Every action goes through the SafetyGuard and is logged. In dry-run mode (default)
nothing is sent, actions are only recorded in `self.history`.
"""
from __future__ import annotations
import logging, sys, time
from .safety import SafetyGuard

log = logging.getLogger(__name__)


def _backend():
    if sys.platform != "win32":
        raise RuntimeError("Real input is only supported on Windows")
    import pydirectinput
    pydirectinput.FAILSAFE = True
    pydirectinput.PAUSE = 0.0
    return pydirectinput


class InputController:
    def __init__(self, safety: SafetyGuard, dry_run: bool = True, backend=None):
        self.safety = safety
        self.dry_run = dry_run
        self._backend = backend
        self.history: list[tuple] = []

    @property
    def backend(self):
        if self._backend is None:
            self._backend = _backend()
        return self._backend

    def _do(self, name, *args):
        self.safety.check()
        self.history.append((name, *args))
        log.info("%s%s %s", "[dry] " if self.dry_run else "", name, args)
        if self.dry_run:
            return
        b = self.backend
        if name == "press":
            b.press(args[0])
        elif name == "key_down":
            b.keyDown(args[0])
        elif name == "key_up":
            b.keyUp(args[0])
        elif name == "click":
            b.click(button=args[0])
        elif name == "move_rel":
            b.moveRel(args[0], args[1], relative=True)
        elif name == "move_to":
            b.moveTo(args[0], args[1])
        elif name == "mouse_down":
            b.mouseDown(button=args[0])
        elif name == "mouse_up":
            b.mouseUp(button=args[0])

    def press(self, key): self._do("press", key)
    def key_down(self, key): self._do("key_down", key)
    def key_up(self, key): self._do("key_up", key)
    def click(self, button="left"): self._do("click", button)
    def mouse_down(self, button="left"): self._do("mouse_down", button)
    def mouse_up(self, button="left"): self._do("mouse_up", button)
    def move_rel(self, dx, dy): self._do("move_rel", int(dx), int(dy))
    def move_to(self, x, y): self._do("move_to", int(x), int(y))

    def hold(self, key, seconds: float):
        self.key_down(key)
        try:
            self.sleep(seconds)
        finally:
            self.release_all_key(key)

    def release_all_key(self, key):
        # release even if stopped
        self.history.append(("key_up", key))
        if not self.dry_run:
            self.backend.keyUp(key)

    def sleep(self, seconds: float):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.safety.check()
            time.sleep(min(0.02, max(0.0, end - time.monotonic())))
