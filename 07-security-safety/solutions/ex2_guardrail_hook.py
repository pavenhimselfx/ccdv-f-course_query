"""
SOLUTION — ex2_guardrail_hook.py — CCDV-F Module 07

Reference solution. See exercises/ex2_guardrail_hook.py for the scenario and
instructions. Read that file first and make a genuine attempt before
comparing against this.

Run with:
    python ex2_guardrail_hook.py
"""

import os
from dataclasses import dataclass
from typing import Any, Dict

ALLOWED_DIRECTORY = "/workspace/project"

EXECUTION_LOG = []


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


@dataclass
class ProposedToolCall:
    tool_name: str
    arguments: Dict[str, Any]


@dataclass
class HookDecision:
    approved: bool
    reason: str


# A denylist of substrings that make a shell command destructive. Simple by
# design for this exercise; a production system would likely pair this with
# an allowlist of specific known-safe commands (default-deny is stronger
# than default-allow-minus-denylist), but this is enough to demonstrate the
# hook mechanism.
DESTRUCTIVE_COMMAND_SUBSTRINGS = [
    "rm -rf",
    "mkfs",
    ":(){:|:&};:",   # fork bomb
    "shutdown",
    "> /dev/sda",
    "dd if=",
]


def _path_is_within_allowed_directory(path: str) -> bool:
    """Resolve both paths to their real, absolute, normalized form before
    comparing. This is the key security detail: a naive
    `path.startswith(ALLOWED_DIRECTORY)` check can be fooled two ways —
    (1) a sibling directory that merely shares the string prefix, e.g.
    "/workspace/project-evil/secrets" starts with "/workspace/project" as a
    STRING but is not actually inside it, and (2) path traversal segments
    like "../../etc/passwd" that only resolve to their true target once
    normalized. os.path.realpath collapses ".." segments and symlinks;
    os.path.commonpath then gives us a directory-aware containment check.
    """
    allowed_real = os.path.realpath(ALLOWED_DIRECTORY)
    target_real = os.path.realpath(path)

    if target_real == allowed_real:
        return True

    try:
        common = os.path.commonpath([allowed_real, target_real])
    except ValueError:
        # Different drives on Windows, or otherwise incomparable paths.
        return False

    return common == allowed_real


def guardrail_hook(call: ProposedToolCall) -> HookDecision:
    """Deterministic pre-execution check. This is exactly the mechanism the
    README (section 3) describes: code OUTSIDE the model's own reasoning
    that gets a chance to approve/block a proposed action before it runs,
    regardless of why the model proposed it (mistake, misunderstanding, or
    a successful prompt injection upstream — the hook doesn't need to know
    or care which).
    """
    if call.tool_name == "delete_file":
        path = call.arguments.get("path", "")
        if _path_is_within_allowed_directory(path):
            return HookDecision(approved=True, reason="path is within the allowed directory")
        return HookDecision(
            approved=False,
            reason=f"path '{path}' resolves outside the allowed directory '{ALLOWED_DIRECTORY}'",
        )

    if call.tool_name == "run_shell_command":
        command = call.arguments.get("command", "")
        lowered = command.lower()
        for bad in DESTRUCTIVE_COMMAND_SUBSTRINGS:
            if bad in lowered:
                return HookDecision(
                    approved=False,
                    reason=f"command matches destructive pattern '{bad}'",
                )
        return HookDecision(approved=True, reason="command did not match any destructive pattern")

    # Default-deny: an unrecognized tool name is rejected rather than passed
    # through. This matters because it means adding a new tool to the agent
    # later can't accidentally bypass the guardrail by omission — every tool
    # must be explicitly handled (or explicitly allowlisted) to run at all.
    return HookDecision(approved=False, reason=f"unknown tool '{call.tool_name}' — default-deny")


def execute_with_guardrail(call: ProposedToolCall) -> str:
    decision = guardrail_hook(call)
    if not decision.approved:
        return f"BLOCKED: {call.tool_name}({call.arguments}) — {decision.reason}"

    impl = TOOL_IMPLEMENTATIONS[call.tool_name]
    return impl(**call.arguments)


def test_allows_safe_delete_inside_allowed_directory():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("delete_file", {"path": "/workspace/project/scratch.tmp"})
    )
    assert "deleted" in result
    assert ("delete_file", "/workspace/project/scratch.tmp") in EXECUTION_LOG
    print("PASS: test_allows_safe_delete_inside_allowed_directory")


def test_blocks_delete_outside_allowed_directory():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("delete_file", {"path": "/etc/passwd"})
    )
    assert result.startswith("BLOCKED")
    assert EXECUTION_LOG == []
    print("PASS: test_blocks_delete_outside_allowed_directory")


def test_blocks_path_traversal_trick():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("delete_file", {"path": "/workspace/project/../../etc/passwd"})
    )
    assert result.startswith("BLOCKED")
    assert EXECUTION_LOG == []
    print("PASS: test_blocks_path_traversal_trick")


def test_blocks_destructive_shell_command():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("run_shell_command", {"command": "rm -rf /"})
    )
    assert result.startswith("BLOCKED")
    assert EXECUTION_LOG == []
    print("PASS: test_blocks_destructive_shell_command")


def test_allows_safe_shell_command():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("run_shell_command", {"command": "ls -la /workspace/project"})
    )
    assert result.startswith("ran:")
    assert len(EXECUTION_LOG) == 1
    print("PASS: test_allows_safe_shell_command")


def test_default_deny_unknown_tool():
    EXECUTION_LOG.clear()
    result = execute_with_guardrail(
        ProposedToolCall("format_disk", {"target": "/dev/sda"})
    )
    assert result.startswith("BLOCKED")
    print("PASS: test_default_deny_unknown_tool")


if __name__ == "__main__":
    test_allows_safe_delete_inside_allowed_directory()
    test_blocks_delete_outside_allowed_directory()
    test_blocks_path_traversal_trick()
    test_blocks_destructive_shell_command()
    test_allows_safe_shell_command()
    test_default_deny_unknown_tool()
    print("\nAll checks completed.")
