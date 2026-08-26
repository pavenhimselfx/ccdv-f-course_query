"""
ex2_guardrail_hook.py — CCDV-F Module 07 (Security and Safety)

SKILL: Claude Hooks — leveraging hooks for guardrails and safety controls to
prevent destructive actions within Claude applications.

SCENARIO
--------
An agent has two tools available: `delete_file(path)` and
`run_shell_command(command)`. Left unchecked, the model deciding to call
either of these is trusted blindly — but per the README (section 3), you
should NOT rely solely on the model's own judgment to prevent a destructive
action. Instead you implement a "hook": deterministic Python code that
intercepts every PROPOSED tool call before it executes, checks it against an
explicit policy, and only allows execution if the policy approves.

This exercise does not require an ANTHROPIC_API_KEY at all — it's pure
Python logic and can be fully completed and tested by reading/reasoning and
running the local test functions at the bottom. (In a real agent framework,
this same "check before executing" function is what you'd wire in as a
pre-tool-use hook.)

Run with:
    python ex2_guardrail_hook.py
"""

from dataclasses import dataclass
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Mock tools an agent might propose to call. In a real system these would
# actually touch the filesystem / shell — here they just record what would
# have happened, so tests can check hook behavior without side effects.
# ---------------------------------------------------------------------------

ALLOWED_DIRECTORY = "/workspace/project"

EXECUTION_LOG = []  # appended to only when a tool call actually executes


def delete_file(path: str) -> str:
    EXECUTION_LOG.append(("delete_file", path))
    return f"deleted {path}"


def run_shell_command(command: str) -> str:
    EXECUTION_LOG.append(("run_shell_command", command))
    return f"ran: {command}"


TOOL_IMPLEMENTATIONS = {
    "delete_file": delete_file,
    "run_shell_command": run_shell_command,
}


# ---------------------------------------------------------------------------
# A "proposed tool call," as an agent framework might hand it to your hook:
# just the tool name and its arguments, before anything has executed.
# ---------------------------------------------------------------------------

@dataclass
class ProposedToolCall:
    tool_name: str
    arguments: Dict[str, Any]


@dataclass
class HookDecision:
    approved: bool
    reason: str


# ---------------------------------------------------------------------------
# TODO 1: Define your destructive-command policy.
#
# Fill in DESTRUCTIVE_COMMAND_SUBSTRINGS with lowercase substrings that
# should cause a `run_shell_command` call to be BLOCKED regardless of path
# (e.g. "rm -rf", "mkfs", ":(){:|:&};:", "shutdown", "> /dev/sda"). Aim for
# at least 4 entries. This is a deliberately simple denylist — in a real
# system you'd likely combine a denylist with an allowlist of specific safe
# commands, but a denylist is enough to demonstrate the hook mechanism here.
# ---------------------------------------------------------------------------

DESTRUCTIVE_COMMAND_SUBSTRINGS = [
    # TODO: add lowercase substrings here, e.g. "rm -rf"
]


# ---------------------------------------------------------------------------
# TODO 2: Implement the hook function.
#
# guardrail_hook(call) should:
#   - For `delete_file`: approve only if call.arguments["path"] is inside
#     ALLOWED_DIRECTORY (use a path-based check — beware of naive string
#     prefix checks that "/workspace/project-evil" would incorrectly pass;
#     a robust check normalizes both paths and confirms the target is
#     ALLOWED_DIRECTORY itself or a path underneath it).
#     Reject with a clear reason otherwise (e.g. path traversal like
#     "../../etc/passwd" resolving outside the allowed directory, or any
#     absolute path outside it).
#   - For `run_shell_command`: reject if the command (case-insensitively)
#     contains any substring from DESTRUCTIVE_COMMAND_SUBSTRINGS. Approve
#     otherwise.
#   - For any other/unknown tool name: reject by default (default-deny,
#     not default-allow — an unrecognized tool call should never sail
#     through un-checked).
#
# Return a HookDecision(approved=..., reason=...).
# ---------------------------------------------------------------------------

def guardrail_hook(call: ProposedToolCall) -> HookDecision:
    """TODO: implement the policy described above."""
    raise NotImplementedError("TODO: implement guardrail_hook")


# ---------------------------------------------------------------------------
# The "agent loop" wrapper: this is what actually calls the hook before
# executing anything. In a real framework, the framework itself would call
# your hook at this point in its tool-execution pipeline — you'd register
# guardrail_hook() as a pre-tool-use callback rather than writing this
# execute_with_guardrail() wrapper by hand. It's spelled out here so the
# mechanism is visible.
# ---------------------------------------------------------------------------

def execute_with_guardrail(call: ProposedToolCall) -> str:
    decision = guardrail_hook(call)
    if not decision.approved:
        return f"BLOCKED: {call.tool_name}({call.arguments}) — {decision.reason}"

    impl = TOOL_IMPLEMENTATIONS[call.tool_name]
    return impl(**call.arguments)


# ---------------------------------------------------------------------------
# Tests — no API key needed. These should pass once TODOs 1-2 are done.
# ---------------------------------------------------------------------------

def test_allows_safe_delete_inside_allowed_directory():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("delete_file", {"path": "/workspace/project/scratch.tmp"})
    )
    assert "deleted" in result, f"expected the delete to be approved, got: {result}"
    assert ("delete_file", "/workspace/project/scratch.tmp") in EXECUTION_LOG
    print("PASS: test_allows_safe_delete_inside_allowed_directory")


def test_blocks_delete_outside_allowed_directory():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("delete_file", {"path": "/etc/passwd"})
    )
    assert result.startswith("BLOCKED"), f"expected block, got: {result}"
    assert EXECUTION_LOG == [], "the destructive call must NOT have executed"
    print("PASS: test_blocks_delete_outside_allowed_directory")


def test_blocks_path_traversal_trick():
    """A naive 'startswith(ALLOWED_DIRECTORY)' check can be fooled by a
    sibling directory whose name happens to share the prefix, or by '..'
    segments. Your hook should resolve/normalize the path first."""
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("delete_file", {"path": "/workspace/project/../../etc/passwd"})
    )
    assert result.startswith("BLOCKED"), f"expected traversal to be blocked, got: {result}"
    assert EXECUTION_LOG == []
    print("PASS: test_blocks_path_traversal_trick")


def test_blocks_destructive_shell_command():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("run_shell_command", {"command": "rm -rf /"})
    )
    assert result.startswith("BLOCKED"), f"expected block, got: {result}"
    assert EXECUTION_LOG == []
    print("PASS: test_blocks_destructive_shell_command")


def test_allows_safe_shell_command():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("run_shell_command", {"command": "ls -la /workspace/project"})
    )
    assert result.startswith("ran:"), f"expected approval, got: {result}"
    assert len(EXECUTION_LOG) == 1
    print("PASS: test_allows_safe_shell_command")


def test_default_deny_unknown_tool():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("format_disk", {"target": "/dev/sda"})
    )
    assert result.startswith("BLOCKED"), (
        "unknown tools must be default-denied, not default-allowed"
    )
    print("PASS: test_default_deny_unknown_tool")


if __name__ == "__main__":
    test_allows_safe_delete_inside_allowed_directory()
    test_blocks_delete_outside_allowed_directory()
    test_blocks_path_traversal_trick()
    test_blocks_destructive_shell_command()
    test_allows_safe_shell_command()
    test_default_deny_unknown_tool()
    print("\nAll checks completed.")
