# Portfolio — AI Solutions Integrator

A self-contained portfolio for AI Integration Specialist / AI-Assisted Developer roles.

## Files

| File | What it is |
|---|---|
| `resume.md` | The resume (Markdown → paste into a PDF/ATS-friendly doc) |
| `index.html` | Single-page portfolio site (open in a browser, or deploy to Vercel/Netlify/GitHub Pages) |
| `argus_mcp_server.py` | A Model Context Protocol (MCP) server exposing Argus threat tools to any AI agent |

## Before you ship it

Name, email, phone, and location are filled in. Remaining placeholder to replace:

- `[github.com/username]` / `[username]` — create a free GitHub account first

## The MCP server (the portfolio centerpiece)

`argus_mcp_server.py` wraps Argus's scoring/decision engine into two MCP tools:

- `score_process(image, command_line, parent_image)` → threat score, verdict, severity, matched techniques.
- `sandbox_status()` → the detonation-chamber state (VM, sinkhole, kill-switches, Sysmon).

### Try it

```powershell
cd C:\workspace\portfolio
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' | py argus_mcp_server.py
```

Then call the tools:

```powershell
'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"score_process","arguments":{"image":"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe","command_line":"powershell.exe -nop -w hidden -enc SQBFAFgA","parent_image":"cmd.exe"}}}' | py argus_mcp_server.py
```

### Register with an MCP client

Add to `claude_desktop_config.json` (or your client's equivalent):

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

### Record a 2-minute demo

Screen-record: you ask an agent *"is this PowerShell command suspicious?"* → the agent calls `score_process` → Argus returns the score + verdict + techniques. That single clip, on top of the repo, is the strongest hiring signal for "AI Integration Specialist" roles.
