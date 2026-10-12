from .base import Skill, register


@register
class Kickoff(Skill):
    name = "rl_kickoff"; game = "rocket_league"
    description = "Speed-flip style kickoff: boost forward, jump + flip into ball."
    params = {"drive": "seconds to boost (default 1.6)"}
    def run(self, ctx, drive=1.6, **_):
        t, b = ctx.profile.key("throttle"), ctx.profile.key("boost")
        ctx.input.key_down(t); ctx.input.mouse_down(b)
        try:
            ctx.input.sleep(float(drive))
            j = ctx.profile.key("jump")
            ctx.input.click(j); ctx.input.sleep(0.08); ctx.input.click(j)
            ctx.input.sleep(0.5)
        finally:
            ctx.input.mouse_up(b); ctx.input.release_all_key(t)
        return "Kickoff done"


@register
class HalfFlip(Skill):
    name = "rl_half_flip"; game = "rocket_league"; description = "Half-flip to turn around fast."
    def run(self, ctx, **_):
        j, r = ctx.profile.key("jump"), ctx.profile.key("reverse")
        ctx.input.key_down(r); ctx.input.click(j); ctx.input.sleep(0.1); ctx.input.click(j)
        ctx.input.sleep(0.15); ctx.input.release_all_key(r)
        self.hold(ctx, "throttle", 0.4)
        return "Half flip"


@register
class BoostDrive(Skill):
    name = "rl_boost"; game = "rocket_league"; description = "Boost forward for N seconds."
    params = {"seconds": "default 1"}
    def run(self, ctx, seconds=1, **_):
        ctx.input.key_down(ctx.profile.key("throttle"))
        try:
            self.hold(ctx, "boost", float(seconds))
        finally:
            ctx.input.release_all_key(ctx.profile.key("throttle"))
        return "Boosted"
