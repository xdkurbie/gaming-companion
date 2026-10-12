"""Screen capture (mss) -> PIL image / PNG / base64."""
from __future__ import annotations
import base64, io


class ScreenCapture:
    def __init__(self, monitor: int = 1):
        self.monitor = monitor

    def grab(self, region: tuple[int, int, int, int] | None = None):
        import mss
        from PIL import Image
        with mss.mss() as sct:
            mon = sct.monitors[min(self.monitor, len(sct.monitors) - 1)]
            if region:
                x, y, w, h = region
                mon = {"left": mon["left"] + x, "top": mon["top"] + y, "width": w, "height": h}
            shot = sct.grab(mon)
            return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    @staticmethod
    def to_base64_png(img, max_side: int = 1280) -> str:
        img = img.copy()
        img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
