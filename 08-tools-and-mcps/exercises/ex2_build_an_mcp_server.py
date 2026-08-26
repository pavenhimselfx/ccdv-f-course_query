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

# TODO: import the high-level server class. As of this writing the common
# pattern is:
#
#     from mcp.server.fastmcp import FastMCP
#
# but double-check against current docs/installed package - this import
# path is exactly the kind of detail that can shift between SDK versions.


# TODO: construct the server object, giving it a name that will identify it
# to any MCP client that connects (e.g. "time-and-info-server").
#
#     mcp_server = FastMCP("time-and-info-server")


# ---------------------------------------------------------------------------
# TOOL: get_current_time
# ---------------------------------------------------------------------------

# TODO: register this function as a TOOL using the server object's tool
# decorator (commonly @mcp_server.tool()). Notice this looks almost exactly
# like a client-side Anthropic tool from Exercise 1 in shape (name +
# description via docstring + typed parameters) - the SDK typically infers
# the JSON Schema from the Python type hints and uses the docstring as the
# description, which is why BOTH still matter: write a clear docstring the
# same way you'd write a tool "description" in Exercise 1.
def get_current_time(timezone_offset_hours: int = 0) -> str:
    """Get the current time, shifted by a whole-hour UTC offset.

    Args:
        timezone_offset_hours: Hours to add to UTC (e.g. -5 for US Eastern
            standard time, 0 for UTC itself). Defaults to 0 (UTC).

    Returns:
        An ISO-8601-ish timestamp string reflecting the shifted time.
    """
    # TODO: compute now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset_hours)
    # and return an isoformat() string (or similarly formatted string).
    raise NotImplementedError("TODO: implement get_current_time")


# ---------------------------------------------------------------------------
# RESOURCE: server-info://about
# ---------------------------------------------------------------------------

# TODO: register this function as a RESOURCE using the server object's
# resource decorator with a URI, e.g. @mcp_server.resource("server-info://about")
# Resources are for READ-ONLY CONTEXT, not actions - notice this function
# takes NO caller-supplied arguments, unlike the tool above.
def about_this_server() -> str:
    """Static description of this MCP server, returned when a client reads
    the server-info://about resource."""
    # TODO: return a short multi-line string: name, one-sentence purpose,
    # and a list of what it exposes (1 tool: get_current_time; 1 resource:
    # this one). This is the kind of thing a client might show a user or
    # feed to Claude as background context about what this server offers.
    raise NotImplementedError("TODO: implement about_this_server")


# ---------------------------------------------------------------------------
# BONUS: PROMPT (optional)
# ---------------------------------------------------------------------------

# TODO (optional, bonus): if your installed SDK version supports a prompt
# decorator (commonly @mcp_server.prompt()), register a "time_report"
# prompt template that produces a message asking Claude to phrase the
# current time in a friendly, conversational sentence. This demonstrates
# the THIRD MCP primitive (README.md 2.2): a reusable, possibly
# parameterized prompt template the server hands to any connected client,
# rather than a tool (action) or a resource (context data).


# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # TODO: run the server over stdio - the standard transport for a
    # locally-launched, process-based MCP server (README.md 2.4). Commonly:
    #
    #     mcp_server.run()          # often defaults to stdio
    #   or
    #     mcp_server.run(transport="stdio")
    #
    # Check current SDK docs for the exact call. Until this TODO is done,
    # this script intentionally does nothing when run directly.
    print(
        "TODO: call mcp_server.run() (or the current SDK's equivalent) "
        "here to actually start serving over stdio."
    )

# ---------------------------------------------------------------------------
# NEXT: TEST THIS SERVER FOR FREE
# ---------------------------------------------------------------------------
# Once the TODOs above are filled in, don't reach for a bespoke Python MCP
# test client. See ex2b_test_with_claude_code.md in this same folder: it
# walks through connecting this exact server to Claude Code (authenticated
# against a Team/Enterprise Claude.ai subscription) and testing it
# conversationally - a real MCP client, zero metered API calls.
