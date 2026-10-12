# Gaming Companion

An AI gaming companion for Windows that **reads your screen**, **sends keyboard/mouse input**, **learns how you play**, and runs **skills** for Elden Ring, Dune Awakening and Rocket League. It can use any OpenAI-compatible LLM/VLM (OpenAI, Perplexity, Hugging Face router, Ollama/LM Studio locally) and talk to **MCP addons** such as REA (reverse engineer anything). It also runs as an MCP server, so other AI agents can drive it.

> For fun, learning and **offline** play only. Automated input in online matches can break game ToS and trigger anti-cheat bans.

## Download
Get `GamingCompanion.exe` from [Releases](../../releases) and double-click it (GUI). Other modes:
```
GamingCompanion.exe skills   # list skills
GamingCompanion.exe mcp      # run as MCP server over stdio
```

## Features
| Layer | Module | Details |
|---|---|---|
| Perception | `perception.py` | `mss` screen capture -> PNG/base64 for the VLM |
| Input | `input_controller.py` | `pydirectinput` (DirectInput scan codes, works in games). Dry-run by default |
| Safety | `safety.py` | Global emergency stop hotkey (F12, via `pynput`), STOP button, keys released on stop |
| AI | `vlm.py` | OpenAI-compatible chat + images: tips, and natural-language goal -> JSON action plan restricted to known keybinds |
| Learning | `recorder.py` | Records your input, replays it, and builds a playstyle model (key frequency, hold times, transitions) to imitate you |
| Skills | `skills/` | Per-game plugins + profiles with editable keybinds (`profiles/*.json`, overrides in config) |
| Addons | `mcp_client.py` | MCP stdio client; configure any server (e.g. REA) in settings |
| GUI | `gui.py` | Tkinter: game picker, skills, "Do it" command box, Get tip, recording, settings |
| Server | `server.py` | MCP tools: list_skills, set_game, run_skill, screenshot, get_tip, emergency_stop |

### Skills
- **Elden Ring:** `er_mount_torrent`, `er_ride_to_grace` (mount + gallop, VLM steering toward the guidance light), `er_fast_travel` (open map, move cursor, travel), `er_dodge`
- **Dune Awakening:** `dune_sprint`, `dune_map`, `dune_suspensor_jump`
- **Rocket League:** `rl_kickoff`, `rl_half_flip`, `rl_boost`
- **All games:** `replay_recording`, `imitate_playstyle`

## Setup
Settings are stored in `%USERPROFILE%\.gaming_companion\config.json` (edit in the GUI under *Settings*):
```json
{
  "dry_run": true,
  "emergency_stop_hotkey": "f12",
  "llm": {"provider": "perplexity", "base_url": "https://api.perplexity.ai", "model": "sonar-pro", "api_key": "..."},
  "keybind_overrides": {"elden_ring": {"torrent": "e"}},
  "mcp_addons": {"rea": {"command": ["node", "C:/tools/rea/dist/index.js"]}}
}
```
API keys can also come from `GC_API_KEY`, `OPENAI_API_KEY`, `PERPLEXITY_API_KEY` or `HF_TOKEN`. Example providers:
- Hugging Face: `base_url` `https://router.huggingface.co/v1`, a vision model like `Qwen/Qwen2.5-VL-7B-Instruct`
- Local: Ollama `http://localhost:11434/v1`, model `llava` or `qwen2.5vl`

Untick **Dry-run** in the GUI to send real input. Skills start after a 3 s delay so you can focus the game window. Press **F12** to stop instantly. Some games need the companion to run as Administrator to accept input.

### From source
```
pip install -e ".[dev]"
python -m pytest
python -m gaming_companion
```

## Honest status
- **Implemented & unit-tested (Linux CI with mocks + Windows CI):** config, safety stop, input controller (dry/real paths), skill registry and all skills' input sequences, VLM request/plan parsing, recording/replay/playstyle model, MCP client (against a fake server), MCP server construction.
- **Not verified against the real games:** the keybinds are defaults and skill timings are best guesses; adjust them to your settings. VLM steering quality depends on the model you pick. Playstyle imitation is statistical (it copies key patterns and timing), not a trained neural agent.
- **REA:** works through the generic MCP client; you install REA yourself and set its launch command.
