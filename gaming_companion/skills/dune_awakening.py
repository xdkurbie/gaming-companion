from .base import Skill, register


@register
class SprintTo(Skill):
    name = "dune_sprint"; game = "dune_awakening"
    description = "Sprint forward for N seconds (crouch-stop to break sandworm attention)."
    params = {"seconds": "default 5"}
    def run(self, ctx, seconds=5, **_):
        ctx.input.key_down(ctx.profile.key("sprint"))
        try:
            self.hold(ctx, "forward", float(seconds))
        finally:
            ctx.input.release_all_key(ctx.profile.key("sprint"))
        return f"Sprinted {seconds}s"


@register
class OpenMap(Skill):
    name = "dune_map"; game = "dune_awakening"; description = "Open the map."
    def run(self, ctx, **_):
        self.tap(ctx, "map"); return "Map opened"


@register
class SuspensorJump(Skill):
    name = "dune_suspensor_jump"; game = "dune_awakening"
    description = "Jump then activate suspensor belt to glide."
    def run(self, ctx, **_):
        self.tap(ctx, "jump"); ctx.input.sleep(0.3); self.hold(ctx, "suspensor", 1.5)
        return "Suspensor jump"
