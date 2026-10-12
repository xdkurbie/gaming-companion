from .base import Skill, register


@register
class SummonTorrent(Skill):
    name = "er_mount_torrent"; game = "elden_ring"
    description = "Use the Spectral Steed Whistle to mount Torrent."
    def run(self, ctx, **_):
        self.tap(ctx, "torrent"); ctx.input.sleep(1.5)
        return "Summoned Torrent"


@register
class RideToGrace(Skill):
    name = "er_ride_to_grace"; game = "elden_ring"
    description = "Mount Torrent and ride toward the nearest Site of Grace (follows the guidance light, optionally VLM-steered)."
    params = {"seconds": "riding time (default 10)", "use_vision": "steer with VLM (default true)"}
    def run(self, ctx, seconds=10, use_vision=True, **_):
        SummonTorrent().run(ctx)
        ctx.input.key_down(ctx.profile.key("forward"))
        ctx.input.key_down(ctx.profile.key("dash"))  # gallop
        try:
            elapsed = 0.0
            while elapsed < float(seconds):
                if use_vision and ctx.vlm and ctx.capture:
                    try:
                        hint = ctx.vlm.chat("Is the golden guidance light / grace to the LEFT, RIGHT or AHEAD? one word.",
                                            ctx.screenshot_b64()).strip().upper()
                        if "LEFT" in hint: ctx.input.move_rel(-150, 0)
                        elif "RIGHT" in hint: ctx.input.move_rel(150, 0)
                    except Exception:
                        use_vision = False
                ctx.input.sleep(1.0); elapsed += 1.0
        finally:
            ctx.input.release_all_key(ctx.profile.key("dash"))
            ctx.input.release_all_key(ctx.profile.key("forward"))
        return f"Rode for {seconds}s toward grace"


@register
class FastTravelMap(Skill):
    name = "er_fast_travel"; game = "elden_ring"
    description = "Open the map and fast travel to the grace under the cursor (moves cursor dx/dy steps first)."
    params = {"dx": "cursor steps right (neg=left)", "dy": "cursor steps down (neg=up)"}
    def run(self, ctx, dx=0, dy=0, **_):
        self.tap(ctx, "map"); ctx.input.sleep(1.0)
        dx, dy = int(dx), int(dy)
        self.tap(ctx, "map_cursor_right" if dx > 0 else "map_cursor_left", abs(dx))
        self.tap(ctx, "map_cursor_down" if dy > 0 else "map_cursor_up", abs(dy))
        self.tap(ctx, "fast_travel"); ctx.input.sleep(0.5); self.tap(ctx, "confirm")
        return "Fast travel requested"


@register
class DodgeRoll(Skill):
    name = "er_dodge"; game = "elden_ring"; description = "Dodge roll."
    def run(self, ctx, **_):
        self.tap(ctx, "dash"); return "Rolled"
