import json, sys, textwrap
from unittest.mock import MagicMock
import pytest
from gaming_companion.config import Config, LLMConfig
from gaming_companion.brain import GameBrain
from gaming_companion.safety import SafetyGuard, EmergencyStop
from gaming_companion.input_controller import InputController
from gaming_companion.recorder import PlaystyleModel, replay
from gaming_companion.vlm import VLMAdapter, parse_plan
from gaming_companion.mcp_client import MCPClient
from gaming_companion.skills import load_profile


def brain(game="elden_ring", vlm=None, dry=True):
    cap = MagicMock(); cap.to_base64_png.return_value = "x"
    return GameBrain(Config(dry_run=dry), game, backend=MagicMock(), capture=cap, vlm=vlm or MagicMock())


def test_profiles_load_with_override():
    p = load_profile("rocket_league", {"boost": "b"})
    assert p.key("boost") == "b" and p.key("throttle") == "w"


@pytest.mark.parametrize("game", ["elden_ring", "dune_awakening", "rocket_league"])
def test_all_skills_run_dry(game, tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    b = brain(game)
    b.vlm.chat.return_value = "LEFT"
    for name in b.skills():
        if name in ("replay_recording", "imitate_playstyle"): continue
        params = {"seconds": 0.05} if "seconds" in b.skills()[name].params else {}
        if name == "rl_kickoff": params = {"drive": 0.01}
        assert "Stopped" not in b.run_skill(name, **params)
    assert b.input.history


def test_real_mode_calls_backend():
    b = brain(dry=False)
    b.run_skill("er_dodge")
    b.input.backend.press.assert_called_with("space")


def test_emergency_stop():
    s = SafetyGuard(); c = InputController(s)
    s.trigger()
    with pytest.raises(EmergencyStop): c.press("w")


def test_playstyle_learn_and_imitate(tmp_path):
    ev = [{"t": 0, "kind": "down", "key": "w"}, {"t": 0.5, "kind": "up", "key": "w"},
          {"t": 0.6, "kind": "down", "key": "space"}, {"t": 0.7, "kind": "up", "key": "space"},
          {"t": 0.8, "kind": "down", "key": "w"}, {"t": 1.3, "kind": "up", "key": "w"}]
    m = PlaystyleModel().fit(ev)
    assert m.freq["w"] == 2 and abs(m.avg_hold("w") - 0.5) < 1e-6
    assert m.generate(5)
    f = tmp_path / "r.json"; f.write_text(json.dumps(ev))
    b = brain(); b.input.sleep = lambda s: None
    assert "w" in b.run_skill("imitate_playstyle", path=str(f), steps=3)
    c = InputController(SafetyGuard()); c.sleep = lambda s: None; replay(ev, c)
    assert c.history[0] == ("key_down", "w")


def test_vlm_request_and_plan():
    sess = MagicMock()
    sess.post.return_value.json.return_value = {"choices": [{"message": {"content": 'ok [{"action":"forward","seconds":2},{"action":"hack","seconds":1}]'}}]}
    v = VLMAdapter(LLMConfig(provider="perplexity", base_url="https://api.perplexity.ai", api_key="k"), session=sess)
    plan = v.plan_actions("Elden Ring", "go", ["forward"], "img")
    assert plan == [{"action": "forward", "seconds": 2.0}]
    args, kw = sess.post.call_args
    assert args[0] == "https://api.perplexity.ai/chat/completions"
    assert kw["headers"]["Authorization"] == "Bearer k"
    assert parse_plan("garbage", ["x"]) == []


def test_do_uses_vlm_plan(monkeypatch):
    v = MagicMock(); v.plan_actions.return_value = [{"action": "forward", "seconds": 0.01}]
    b = brain("dune_awakening", vlm=v)
    assert "1 planned" in b.do("walk somewhere unusual")


FAKE_SERVER = textwrap.dedent('''
import sys, json
for line in sys.stdin:
    m = json.loads(line)
    if "id" not in m: continue
    if m["method"] == "initialize": r = {"capabilities": {}}
    elif m["method"] == "tools/list": r = {"tools": [{"name": "echo"}]}
    else: r = {"content": [{"type": "text", "text": "echo:" + m["params"]["arguments"]["x"]}]}
    print(json.dumps({"jsonrpc": "2.0", "id": m["id"], "result": r}), flush=True)
''')


def test_mcp_client(tmp_path):
    s = tmp_path / "srv.py"; s.write_text(FAKE_SERVER)
    with MCPClient([sys.executable, str(s)]) as c:
        assert c.list_tools()[0]["name"] == "echo"
        assert c.call_tool("echo", {"x": "hi"}) == "echo:hi"


def test_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pk")
    c = Config(); c.llm.provider = "perplexity"; p = c.save(tmp_path / "c.json")
    assert Config.load(p).llm.api_key == "pk"


def test_mcp_server_builds():
    pytest.importorskip("mcp")
    from gaming_companion.server import build_server
    assert build_server(brain()) is not None
