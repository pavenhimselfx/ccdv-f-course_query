"""
SOLUTION - Exercise 2: Build a Minimal MCP Server
====================================================
Domain 8 (Tools and MCPs) - Skill: MCP Server Development (2.1%)

See exercises/ex2_build_an_mcp_server.py for the full task description.

SDK CURRENCY WARNING (repeated from the exercise, because it matters): this
solution is written against the common `mcp.server.fastmcp.FastMCP`
high-level pattern as of early-to-mid 2026. Decorator names, import paths,
and exact run() signatures for the `mcp` Python SDK can and do change.
Before relying on this in a real project, verify against:
  - https://modelcontextprotocol.io
  - the docstrings/help of whatever `mcp` version you actually have installed
The STRUCTURE (server object, decorator-based registration of tools /
resources / prompts, run-over-stdio entrypoint) is the exam-relevant,
durable part of this solution - not the exact spelling of each call.

INSTALL: pip install mcp
INSPECT (per current SDK docs, subject to change): mcp dev ex2_build_an_mcp_server.py
"""

from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP

# The server object is the central registry: every tool/resource/prompt
# below attaches to it via decorators, and it's what run() ultimately
# serves to a connecting client. The name given here ("time-and-info-
# server") is how a client identifies this server (e.g. in a client's MCP
# server list / logs) - pick something specific enough to recognize later.
mcp_server = FastMCP("time-and-info-server")


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
    # This is a TOOL (an action/computation with a result), not a resource,
    # because it takes a caller-supplied parameter and computes something
    # fresh each call - the MCP analog of a client-side tool from
    # Exercise 1, just executed inside this server process instead of a
    # host application's own code.
    now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset_hours)
    return now.isoformat()


# ---------------------------------------------------------------------------
# RESOURCE: server-info://about
# ---------------------------------------------------------------------------

@mcp_server.resource("server-info://about")
def about_this_server() -> str:
    """Static description of this MCP server, returned when a client reads
    the server-info://about resource."""
    # This is a RESOURCE, not a tool: it takes no caller-supplied
    # arguments and just hands back readable context/data about the
    # server itself - the MCP analog of a GET request against a fixed
    # URI, rather than an action with parameters.
    return (
        "time-and-info-server v1.0\n"
        "Purpose: demonstration MCP server for CCDV-F Domain 8, Exercise 2.\n"
        "Exposes:\n"
        "  - 1 tool: get_current_time(timezone_offset_hours: int = 0)\n"
        "  - 1 resource: server-info://about (this text)\n"
    )


# ---------------------------------------------------------------------------
# BONUS: PROMPT
# ---------------------------------------------------------------------------

@mcp_server.prompt()
def time_report() -> str:
    """Reusable prompt template: ask Claude to phrase the current time in a
    friendly, conversational sentence.

    This is the third MCP primitive: unlike the tool above (an action
    Claude asks the server to execute) and the resource above (static
    context data), a PROMPT is a reusable message template the server
    contributes to a client - e.g. a client's UI might list this as a
    ready-made "/time_report" prompt any user of this server can invoke
    without writing the wording themselves. Real prompt templates are
    often parameterized (accept arguments the client fills in); this one
    is intentionally kept argument-free to stay minimal.
    """
    return (
        "Call the get_current_time tool, then restate the result back to "
        "me as one short, friendly sentence (e.g. 'It's currently around "
        "3:45 in the afternoon, UTC.') rather than a raw timestamp."
    )


# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # stdio is the standard transport for a locally-launched, process-based
    # MCP server (README.md 2.4): whatever client config points at
    # "python ex2_build_an_mcp_server.py" will spawn this exact process and
    # talk to it over its stdin/stdout, with no network/port configuration
    # needed. FastMCP's run() commonly defaults to stdio, but it's spelled
    # out explicitly here for clarity.
    mcp_server.run(transport="stdio")

# ---------------------------------------------------------------------------
# NEXT: TEST THIS SERVER FOR FREE
# ---------------------------------------------------------------------------
# See solutions/ex2b_test_with_claude_code.md for a filled-in .mcp.json
# pointing at this file and a transcript-style example of connecting it to
# Claude Code and calling get_current_time conversationally - a real MCP
# client, zero metered API calls, as long as Claude Code is authenticated
# via CLAUDE_CODE_OAUTH_TOKEN against a Team/Enterprise subscription.
