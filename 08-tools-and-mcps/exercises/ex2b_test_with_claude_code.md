# Exercise 2b: Test Your MCP Server for Free with Claude Code

Domain 8 (Tools and MCPs) - Skill: MCP Server Development (2.1%)

## Why this exercise exists

`ex2_build_an_mcp_server.py` already needs no Anthropic API key at all to
**write or run** - it's a standalone process speaking MCP over stdio, and
nothing about building it touches the Anthropic API. But to actually
**verify** it end-to-end, something has to act as the MCP *client*: connect
to your server, list its tools, call `get_current_time`, and show you what
came back. The natural instinct is to write a small Python script that
imports `anthropic`, defines an MCP-aware client loop, and burns a metered
API call just to sanity-check a server that itself cost nothing.

You don't have to do that. **Claude Code is already a full MCP client**, and
if you're authenticated against a Team/Enterprise Claude.ai subscription (see
`00-setup/README.md` section 1), talking to it costs nothing beyond your
normal subscription usage. This exercise walks through connecting your
Exercise 2 server to Claude Code and testing it conversationally instead of
writing a bespoke test client.

This is genuinely the realistic path, not just the free one: "register a
server with a client's configuration" (README.md 2.3) is exactly what you're
doing, and Claude Code is one of the reference MCP clients the exam expects
you to know about.

## Step 1: register the server with Claude Code

Claude Code discovers MCP servers from a project-level `.mcp.json` file (or
via its own CLI management commands - both roads lead to the same
underlying configuration). A minimal config pointing at your Exercise 2
solution, launched as a local stdio subprocess, looks like this:

```json
{
  "mcpServers": {
    "time-and-info-server": {
      "command": "python",
      "args": ["/absolute/path/to/solutions/ex2_build_an_mcp_server.py"]
    }
  }
}
```

Put a file named `.mcp.json` with that content in the directory you'll run
`claude` from (or wherever your Claude Code setup expects project-level MCP
config - check current docs if this has moved). Use an **absolute path** to
the server script; a relative path is fragile once you `cd` somewhere else.
If your server needs a specific virtual environment's Python, point
`command` at that interpreter's full path (e.g.
`/path/to/.venv/bin/python`) rather than relying on whatever `python`
resolves to in your shell.

**Alternative: `claude mcp add`.** Claude Code also offers a CLI command to
register a server without hand-editing JSON - conceptually something like:

```bash
claude mcp add time-and-info-server -- python /absolute/path/to/solutions/ex2_build_an_mcp_server.py
```

**Check the exact current flags/syntax against
[code.claude.com](https://code.claude.com) before typing this** - `claude
mcp add`'s argument shape (flags for transport, scope, environment
variables, the separator before the launch command) is exactly the kind of
CLI surface that shifts between releases. The concept - "tell Claude Code
the launch command for your stdio server, and it manages the config file for
you" - is the durable part; the precise invocation is not.

## Step 2: launch Claude Code and confirm the server is connected

From the same directory as your `.mcp.json` (or wherever you registered the
server), run:

```bash
claude
```

Once inside the interactive session, ask Claude Code to list its connected
MCP servers (a slash command like `/mcp` is the common way to do this,
though check current docs/help for the exact one) and confirm
`time-and-info-server` shows up as connected, with `get_current_time` listed
among its tools. If it doesn't show up, common causes are: a wrong path in
`.mcp.json`, a Python that doesn't have the `mcp` package installed, or a
syntax error in the server file that crashes it on launch - check the
solution against `ex2_build_an_mcp_server.py`'s own currency warning about
SDK import paths if `mcp.server.fastmcp.FastMCP` doesn't import cleanly on
your installed version.

## Step 3: ask Claude Code to use the tool

Still inside the interactive session, just ask in plain language, e.g.:

> What time is it right now according to the time-and-info-server tool?
> Use UTC.

or, to specifically exercise the offset parameter:

> Use the warehouse... sorry, the time server's get_current_time tool to
> tell me the current time 5 hours behind UTC.

Claude Code will decide to call `get_current_time`, show you the call (and,
depending on your permission settings, may ask you to approve it - this is
the human-in-the-loop approval pattern from README.md 1.5 in action, for a
tool that happens to live in an MCP server rather than your own app code),
execute it against your running server process, and read the result back to
you in a normal sentence. That full round trip - discovery, tool-use
decision, execution against your actual server code, response - is the same
end-to-end thing a bespoke Python MCP client script would have shown you,
with zero metered API calls, because the whole exchange runs on your
Claude.ai subscription's usage instead of a Console API key.

If you implemented the bonus `server-info://about` resource or the
`time_report` prompt, try those too - ask Claude Code to read the resource,
or (if your client surfaces registered prompts, e.g. as a slash command) try
invoking the prompt.

## What "success" looks like

You've verified the server end-to-end once:

1. `claude` starts without an MCP connection error for `time-and-info-server`.
2. Claude Code's tool listing shows `get_current_time` (and, if implemented,
   the resource/prompt) as available.
3. Asking a natural-language question that calls for the tool results in
   Claude actually calling it (not answering from its own guess at the
   current time) and reporting back a time that's plausibly correct for the
   offset you asked for.

See `solutions/ex2b_test_with_claude_code.md` for a filled-in `.mcp.json`
example and a transcript-style example of what a successful interaction
looks like. As always with anything CLI/config-shaped in this module: if
what you see on screen doesn't match this description, trust
[code.claude.com](https://code.claude.com) over this file.
