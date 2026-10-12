"""Expose the companion as an MCP server (stdio) so other AI agents can drive it."""
from __future__ import annotations
from .brain import GameBrain


def build_server(brain: GameBrain | None = None):
    from mcp.server.fastmcp import FastMCP
    brain = brain or GameBrain()
    mcp = FastMCP("gaming-companion")

    @mcp.tool()
    def list_skills() -> dict:
        """List skills for the current game."""
        return {n: c.description for n, c in brain.skills().items()}

    @mcp.tool()
    def set_game(game: str) -> str:
        """Switch game: elden_ring | dune_awakening | rocket_league."""
        brain.set_game(game); return f"Game set to {game}"

    @mcp.tool()
    def run_skill(name: str, params: dict | None = None) -> str:
        """Run a skill by name."""
        return brain.run_skill(name, **(params or {}))

    @mcp.tool()
    def screenshot() -> str:
        """Return the current screen as base64 PNG."""
        return brain.screenshot_b64()

    @mcp.tool()
    def get_tip(question: str = "") -> str:
        """Ask the VLM for a tip based on the current screen."""
        return brain.tip(question)

    @mcp.tool()
    def emergency_stop() -> str:
        """Stop all input immediately."""
        brain.safety.trigger(); return "stopped"

    return mcp


def main():
    build_server().run()


if __name__ == "__main__":
    main()
