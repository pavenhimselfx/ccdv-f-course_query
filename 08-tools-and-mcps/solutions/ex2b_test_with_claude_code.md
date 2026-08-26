# SOLUTION - Exercise 2b: Test Your MCP Server for Free with Claude Code

Domain 8 (Tools and MCPs) - Skill: MCP Server Development (2.1%)

See `exercises/ex2b_test_with_claude_code.md` for the full walkthrough. This
file shows a filled-in `.mcp.json` and an example of what a successful
Claude Code session actually looks like, so you have something concrete to
compare your own run against.

## Filled-in `.mcp.json`

Assuming you cloned/placed this course at `/home/learner/ccdv-f-course` and
are using the `solutions/` version of the Exercise 2 server with a project
virtual environment at `/home/learner/ccdv-f-course/.venv`:

```json
{
  "mcpServers": {
    "time-and-info-server": {
      "command": "/home/learner/ccdv-f-course/.venv/bin/python",
      "args": [
        "/home/learner/ccdv-f-course/08-tools-and-mcps/solutions/ex2_build_an_mcp_server.py"
      ]
    }
  }
}
```

Notes on this example, not requirements - your paths will differ:

- `command` points directly at the venv's Python interpreter rather than a
  bare `python`, so the server launches with the `mcp` package installed
  regardless of what shell/environment Claude Code itself happens to be
  running in.
- `args` is a list because the underlying launch is `exec`-style (command +
  argv), not a shell string - this matters if your path ever needs a space
  or you want to add more arguments later (e.g. an env var flag, if the
  server took one).
- This is a **project-scoped** `.mcp.json` (lives in the directory you run
  `claude` from). Claude Code may also support user-level/global MCP
  registration - check current docs if you want this server available
  everywhere rather than just in this course's directory.

## Example successful transcript

This is illustrative, not a literal captured session - Claude Code's exact
UI chrome (how it renders a tool-call confirmation, the `/mcp` output
formatting) changes over versions and should be checked against
[code.claude.com](https://code.claude.com). The *shape* of the exchange is
the durable part.

```
$ claude
Claude Code v... - MCP servers: time-and-info-server (connected)

> /mcp
Connected MCP servers:
  time-and-info-server
    tools:    get_current_time
    resources: server-info://about
    prompts:   time_report

> Use the time server's get_current_time tool to tell me the current time
> 5 hours behind UTC.

I'll call get_current_time with a -5 hour offset for you.

  [tool call] mcp__time-and-info-server__get_current_time(timezone_offset_hours=-5)
  [tool result] "2026-08-26T09:14:02.118273-05:00" (approximate - reflects
                whatever moment you actually run this)

Right now it's about 9:14 AM, 5 hours behind UTC (2026-08-26T09:14:02-05:00).

> Now read the server-info://about resource and tell me what this server is for.

  [resource read] server-info://about
  [resource content]
    time-and-info-server v1.0
    Purpose: demonstration MCP server for CCDV-F Domain 8, Exercise 2.
    Exposes:
      - 1 tool: get_current_time(timezone_offset_hours: int = 0)
      - 1 resource: server-info://about (this text)

This is a small demonstration MCP server built for Domain 8 of the CCDV-F
course. It exposes one tool - get_current_time, which returns the current
time shifted by a whole-hour UTC offset - and this one resource, which is
just a static description of the server itself.
```

## What this confirms

- **The server actually starts and speaks MCP correctly** - if the JSON-RPC
  handshake, tool schema, or transport wiring were broken, Claude Code would
  fail to connect rather than list the tool, and you'd see a connection
  error instead of the `/mcp` listing above.
- **The tool's JSON Schema (inferred from your type hints/docstring) is
  usable by a real client** - Claude correctly filled in
  `timezone_offset_hours=-5` from a natural-language request, which is the
  same "does the model understand this schema well enough to call it
  correctly" concern from README.md 1.3, just observed through a different
  client than Exercise 1's.
- **The whole exchange - Claude's tool-use decision, Claude Code's dispatch
  to your subprocess, your server's actual Python code running, the result
  flowing back - happened without ever touching a metered Console API key**,
  as long as `claude` was authenticated via `CLAUDE_CODE_OAUTH_TOKEN` against
  a Team/Enterprise subscription rather than `ANTHROPIC_API_KEY`. Run
  `/status` inside Claude Code if you want to double check which credential
  was actually active for this session.
