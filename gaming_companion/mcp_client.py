"""Minimal MCP stdio client (JSON-RPC 2.0, newline-delimited) for addons such
as REA (reverse engineer anything). Addons are configured in config.mcp_addons:
  {"rea": {"command": ["node", "path/to/rea/dist/index.js"], "env": {}}}
"""
from __future__ import annotations
import itertools, json, os, subprocess, threading


class MCPError(RuntimeError):
    pass


class MCPClient:
    def __init__(self, command: list[str], env: dict | None = None, timeout: float = 60.0):
        self.command, self.env, self.timeout = command, env or {}, timeout
        self.proc = None
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def start(self):
        self.proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1,
                                     env={**os.environ, **self.env})
        self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                    "clientInfo": {"name": "gaming-companion", "version": "1.0.0"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return self

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None):
        with self._lock:
            rid = next(self._ids)
            self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
            while True:
                line = self.proc.stdout.readline()
                if not line:
                    raise MCPError("MCP server closed the connection")
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if msg.get("id") == rid:
                    if "error" in msg:
                        raise MCPError(msg["error"].get("message", str(msg["error"])))
                    return msg.get("result")

    def list_tools(self):
        return self.request("tools/list").get("tools", [])

    def call_tool(self, name, arguments=None):
        res = self.request("tools/call", {"name": name, "arguments": arguments or {}})
        return "\n".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")

    def close(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

    def __enter__(self): return self.start()
    def __exit__(self, *a): self.close()


class AddonManager:
    def __init__(self, addons: dict):
        self.addons = addons
        self.clients: dict[str, MCPClient] = {}

    def get(self, name) -> MCPClient:
        if name not in self.clients:
            spec = self.addons.get(name)
            if not spec:
                raise MCPError(f"Addon '{name}' not configured")
            self.clients[name] = MCPClient(spec["command"], spec.get("env")).start()
        return self.clients[name]

    def close_all(self):
        for c in self.clients.values():
            c.close()
        self.clients.clear()
