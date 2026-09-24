# Argus MCP server

`argus_mcp_server.py` wraps Argus's scoring/decision engine into two MCP tools:

- `score_process(image, command_line, parent_image)` → threat score, verdict, severity, matched techniques.
- `sandbox_status()` → detonation-chamber state (VM, sinkhole, kill-switches, Sysmon).

## Try it

```powershell
py argus_mcp_server.py < payload.json
```

Initialize first:

```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' | py argus_mcp_server.py
```

Then call a tool:

```powershell
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"score_process","arguments":{"image":"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe","command_line":"powershell.exe -nop -w hidden -enc SQBFAFgA","parent_image":"cmd.exe"}}}' | py argus_mcp_server.py
```

## Register with an MCP client

Add to `claude_desktop_config.json` (or your client's equivalent) — adjust the path to where this file lives:

```json
{
  "mcpServers": {
    "argus": {
      "command": "py",
      "args": ["C:\\workspace\\portfolio\\argus_mcp_server.py"]
    }
  }
}
```

## Demo

The clearest way to show this working end-to-end is a short screen recording: ask an
agent *"is this PowerShell command suspicious?"*, it calls `score_process`, and Argus
returns the score, verdict, and techniques.
