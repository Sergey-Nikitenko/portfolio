#!/usr/bin/env python3
"""Argus MCP server — expose Argus threat-intelligence tools to any MCP client.

Wraps Argus's scoring/decision engine as Model Context Protocol (MCP) tools, so an
AI agent (Claude Desktop, Cursor, etc.) can ask Argus to score a process event or
report the detonation-sandbox status. Stdlib-only; speaks JSON-RPC 2.0 over stdio.

Run:
    py argus_mcp_server.py

Then register it in your MCP client (e.g. Claude Desktop `claude_desktop_config.json`):
    {
      "mcpServers": {
        "argus": { "command": "py", "args": ["/path/to/portfolio/argus_mcp_server.py"] }
      }
    }
"""
from __future__ import annotations

import json
import os
import sys

SERVER_NAME = "argus"
SERVER_VERSION = "0.1.0"

# The Argus repo path — the one per-instance seam. Defaults to a sibling checkout
# of the Argus repo next to this portfolio; override with the ARGUS_REPO env var.
ARGUS_REPO = os.environ.get("ARGUS_REPO") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "argus"
)


def _ensure_argus():
    if ARGUS_REPO not in sys.path:
        sys.path.insert(0, ARGUS_REPO)


TOOLS = [
    {
        "name": "score_process",
        "description": (
            "Score a process-creation event with Argus's threat heuristics and return "
            "the verdict (allow / flag / propose / quarantine), severity, matched "
            "techniques, and the reasons. Use this to answer 'is this command line "
            "suspicious, and why?'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image": {"type": "string",
                          "description": "Executable path (e.g. C:\\Windows\\System32\\cmd.exe)"},
                "command_line": {"type": "string", "description": "Full command line"},
                "parent_image": {"type": "string",
                                 "description": "Parent process image (optional)"},
            },
            "required": ["image", "command_line"],
        },
    },
    {
        "name": "sandbox_status",
        "description": (
            "Report the Argus malware-sandbox configuration and live VM state "
            "(detonation chamber, sinkhole, kill-switches, Sysmon telemetry)."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def score_process(args: dict) -> dict:
    _ensure_argus()
    from argus.events import ProcessEvent
    from argus.score import score_event
    from argus.engine import decide, severity
    from argus.config import Config

    ev = ProcessEvent(
        source="mcp", event_id=1, timestamp="", pid=0, parent_pid=0,
        image=args.get("image", ""),
        command_line=args.get("command_line", ""),
        parent_image=args.get("parent_image", ""),
    )
    score = score_event(ev)
    cfg = Config()
    return {
        "score": score.points,
        "severity": severity(score.points),
        "decision": decide(score, cfg),
        "reasons": score.reasons,
        "techniques": score.techniques_deduped(),
    }


def sandbox_status(args: dict) -> dict:
    status = {
        "chamber": "argus-det (Windows 11 guest on KVM)",
        "clean_snapshot": "argus-clean",
        "sinkhole_network": "argus-sink (isolated bridge, FakeDNS -> 10.0.0.1)",
        "kill_switches": (
            "L1 egress firewall, L2 injection guard, L3 device guard, "
            "L4 hypervisor guard, L5 detonation timeout"
        ),
        "telemetry": "Sysmon event IDs 1/3/6/9/11/12/13/14/22",
    }
    # Best-effort live VM state via libvirt (read-only); fail-soft if unreachable.
    try:
        import subprocess
        r = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "sudo", "-n", "virsh", "list", "--all"],
            capture_output=True, text=True, timeout=25,
        )
        status["vm_state"] = (r.stdout or r.stderr).strip()
    except Exception as exc:  # noqa: BLE001
        status["vm_state"] = f"unreachable ({type(exc).__name__})"
    return status


_DISPATCH = {"score_process": score_process, "sandbox_status": sandbox_status}


def _result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(req: dict):
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        return _result(req_id, {
            "protocolVersion": params.get("protocolVersion", "2024-11-05"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
    if method == "tools/list":
        return _result(req_id, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = _DISPATCH.get(name)
        if fn is None:
            return _error(req_id, -32602, f"unknown tool: {name}")
        try:
            out = fn(args)
            return _result(req_id, {
                "content": [{"type": "text", "text": json.dumps(out, indent=2)}],
                "isError": False,
            })
        except Exception as exc:  # noqa: BLE001
            return _result(req_id, {
                "content": [{"type": "text", "text": f"error: {type(exc).__name__}: {exc}"}],
                "isError": True,
            })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None  # notifications carry no response
    return _error(req_id, -32601, f"method not found: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req)
        if resp is not None:
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
