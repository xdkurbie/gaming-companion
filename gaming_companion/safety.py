"""Safety layer: global emergency stop + dry-run enforcement."""
from __future__ import annotations
import logging, threading

log = logging.getLogger(__name__)


class EmergencyStop(Exception):
    pass


class SafetyGuard:
    def __init__(self, hotkey: str = "f12"):
        self.hotkey = hotkey
        self._stopped = threading.Event()
        self._listener = None

    @property
    def stopped(self) -> bool:
        return self._stopped.is_set()

    def trigger(self):
        log.warning("EMERGENCY STOP triggered")
        self._stopped.set()

    def reset(self):
        self._stopped.clear()

    def check(self):
        if self._stopped.is_set():
            raise EmergencyStop("Emergency stop active")

    def start_hotkey_listener(self) -> bool:
        """Start a global hotkey listener (pynput). Returns False if unavailable."""
        try:
            from pynput import keyboard
        except Exception as e:  # pragma: no cover - platform dependent
            log.info("pynput unavailable, no global hotkey: %s", e)
            return False
        target = getattr(keyboard.Key, self.hotkey.lower(), None) or keyboard.KeyCode.from_char(self.hotkey)

        def on_press(key):
            if key == target:
                self.trigger()
        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.daemon = True
        self._listener.start()
        return True

    def stop_listener(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
