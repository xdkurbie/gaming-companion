import argparse, sys


def main():
    p = argparse.ArgumentParser(prog="gaming-companion")
    p.add_argument("mode", nargs="?", default="gui", choices=["gui", "mcp", "skills"])
    a = p.parse_args()
    if a.mode == "mcp":
        from .server import main as m; m()
    elif a.mode == "skills":
        from .skills import SKILL_CLASSES
        for n, c in SKILL_CLASSES.items(): print(f"{c.game:16} {n:22} {c.description}")
    else:
        from .gui import main as m; m()


if __name__ == "__main__":
    sys.exit(main())
