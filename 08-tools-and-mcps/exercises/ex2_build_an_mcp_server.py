"""
Exercise 2: Build a Minimal MCP Server
========================================
Domain 8 (Tools and MCPs) - Skill: MCP Server Development (2.1%)

THE TASK
--------
Build a small MCP server, exposed over stdio, with:

  - ONE TOOL:      get_current_time(timezone_offset_hours: int = 0) -> str
                    Returns the current UTC time, shifted by the given
                    offset in whole hours, as an ISO-ish string.

  - ONE RESOURCE:  server-info://about
                    A static piece of text describing this server (name,
                    version, what it's for) - resources are for readable
                    CONTEXT, not actions, so no arguments here.

  - (BONUS, optional) ONE PROMPT: a reusable prompt template, e.g.
                    "time_report" that asks Claude to summarize the
                    current time in a friendly sentence. Prompts are
                    reusable message templates a client can surface to a
                    user - try implementing one if your SDK version
                    supports it, but it's not required to complete the
                    exercise.

IMPORTANT SDK NOTE
-------------------
This exercise uses the common high-level pattern from the `mcp` Python SDK
(FastMCP-style: a server object, decorators to register tools/resources/
prompts, and a run() call). Decorator names, import paths, and exact
signatures MAY HAVE CHANGED since this was written - the MCP Python SDK is
actively evolving. Before you run this, check:
  - https://modelcontextprotocol.io  (the official MCP docs)
  - `pip show mcp` / the installed package's own docstrings, if installed
and adjust imports/decorators to match what's actually installed. The
STRUCTURE below (server object -> register tool -> register resource ->
run over stdio) is what the exam cares about; treat the exact API names as
"verify before you ship," per README.md's currency note.

INSTALL
-------
    pip install mcp

RUN
---
This server speaks MCP over stdio, which means it's designed to be
LAUNCHED BY AN MCP CLIENT (Claude Desktop, Claude Code's MCP config, or
the `mcp` SDK's own dev inspector), not run standalone and typed into
interactively. To manually sanity-check it without a full client, the SDK
typically ships a CLI inspector, e.g.:

    mcp dev ex2_build_an_mcp_server.py

(again: check current `mcp` CLI docs/help output - the exact subcommand may
have changed). To wire it into Claude Code or Claude Desktop, you'd add an
entry to that application's MCP server configuration pointing at
`python /path/to/this_file.py` (or the solved solutions/ version) as the
command to launch over stdio.

NO API KEY? An MCP server doesn't call the Anthropic API at all - it's a
standalone process that a CLIENT (which may itself talk to Claude) connects
to. You can build and (if you have the `mcp` package installed) run/inspect
this exercise with NO Claude API key at all. If you don't want to install
anything either, read through the TODOs and write the code you believe is
correct, then compare carefully against solutions/.
"""

from datetime import datetime, timedelta, timezone

# DRIFT FOUND BY ACTUALLY CHECKING THE INSTALLED PACKAGE (mcp 2.1.1): the
# exercise's suggested `from mcp.server.fastmcp import FastMCP` raises
# ModuleNotFoundError on this version -- mcp 2.x renamed FastMCP to
# MCPServer and moved it to mcp.server.mcpserver. The decorator/run() shapes
# below are otherwise the same. Exactly the "verify before you ship" drift
# this exercise's docstring warns about, confirmed for real rather than
# assumed.
from mcp.server.mcpserver import MCPServer

mcp_server = MCPServer("time-and-info-server")


# ---------------------------------------------------------------------------
# TOOL: get_current_time
# ---------------------------------------------------------------------------

@mcp_server.tool()
def get_current_time(timezone_offset_hours: int = 0) -> str:
    """Get the current time, shifted by a whole-hour UTC offset.

    Args:
        timezone_offset_hours: Hours to add to UTC (e.g. -5 for US Eastern
            standard time, 0 for UTC itself). Defaults to 0 (UTC).

    Returns:
        An ISO-8601-ish timestamp string reflecting the shifted time.
    """
    # Not `datetime.now(timezone.utc) + timedelta(hours=offset)`: tested that
    # directly and found it shifts the wall-clock VALUE but leaves the
    # tzinfo label as "+00:00" (UTC) -- producing an ISO string that's
    # actively wrong (it claims to be UTC while showing a non-UTC value).
    # Constructing a real fixed-offset tzinfo instead keeps the represented
    # instant correct AND makes isoformat() print the matching offset.
    shifted_tz = timezone(timedelta(hours=timezone_offset_hours))
    now = datetime.now(shifted_tz)
    return now.isoformat()


# ---------------------------------------------------------------------------
# RESOURCE: server-info://about
# ---------------------------------------------------------------------------

@mcp_server.resource("server-info://about")
def about_this_server() -> str:
    """Static description of this MCP server, returned when a client reads
    the server-info://about resource."""
    return (
        "time-and-info-server\n"
        "A minimal demo MCP server for the CCDV-F course, Domain 8, Exercise 2.\n\n"
        "Exposes:\n"
        "- 1 tool: get_current_time(timezone_offset_hours) -- current UTC time, "
        "shifted by a whole-hour offset.\n"
        "- 1 resource: server-info://about -- this description."
    )


# ---------------------------------------------------------------------------
# BONUS: PROMPT (optional)
# ---------------------------------------------------------------------------

@mcp_server.prompt()
def time_report(timezone_offset_hours: int = 0) -> str:
    """Ask Claude to phrase the current time as a friendly, conversational
    sentence, demonstrating the third MCP primitive (README.md 2.2): a
    reusable prompt template the server hands to any connected client,
    rather than a tool (action) or a resource (context data)."""
    current_time = get_current_time(timezone_offset_hours)
    return (
        f"The current time (UTC{timezone_offset_hours:+d}) is {current_time}. "
        "Summarize this for the user in one friendly, conversational sentence."
    )


# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp_server.run(transport="stdio")

# ---------------------------------------------------------------------------
# NEXT: TEST THIS SERVER FOR FREE
# ---------------------------------------------------------------------------
# Once the TODOs above are filled in, don't reach for a bespoke Python MCP
# test client. See ex2b_test_with_claude_code.md in this same folder: it
# walks through connecting this exact server to Claude Code (authenticated
# against a Team/Enterprise Claude.ai subscription) and testing it
# conversationally - a real MCP client, zero metered API calls.
