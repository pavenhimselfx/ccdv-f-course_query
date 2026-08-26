"""
SOLUTION - Exercise 3: Manager / Subagent Pattern

Assumptions about the `claude-agent-sdk` Python package (verify against
code.claude.com if drifted - this SDK moves fast): `query(prompt=...,
options=ClaudeAgentOptions(system_prompt=...))` is an async generator; text
output arrives as `AssistantMessage` objects whose `.content` is a list of
blocks, with `TextBlock` blocks carrying `.text`. Authenticates via
CLAUDE_CODE_OAUTH_TOKEN (see 00-setup/README.md section 1) against a
Claude.ai subscription rather than a metered ANTHROPIC_API_KEY.
"""

import asyncio
import json

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

PRODUCT_DESCRIPTION = (
    "A browser extension that automatically summarizes and flags the key "
    "clauses (renewal terms, cancellation windows, price changes) in any "
    "online subscription agreement or terms-of-service page before you "
    "click 'agree'."
)


async def call_claude(system: str, user: str) -> str:
    """One isolated, single-turn call - every caller of this function gets a
    brand-new `query()` call with no shared history, which is the whole
    point for the subagent calls below: isolation falls out of "start a new
    call" rather than requiring any explicit context-clearing step."""
    options = ClaudeAgentOptions(system_prompt=system)
    chunks = []
    async for message in query(prompt=user, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks).strip()


async def manager_decompose(goal: str) -> list[str]:
    system = (
        "You are a project manager breaking a research task into exactly 3 "
        "independent subtasks. Respond with ONLY a JSON array of 3 short "
        "strings (no other text, no markdown fences)."
    )
    user = (
        f"Goal: {goal}\n\n"
        "Break this into exactly 3 subtasks: one about likely customer pain "
        "points, one about the competitive landscape, and one about a "
        "skeptical buyer's likely objection or risk concern. Each subtask "
        "description should be self-contained enough that someone with NO "
        "other context could work on it."
    )
    raw = await call_claude(system, user)
    try:
        subtasks = json.loads(raw)
    except json.JSONDecodeError:
        # Deterministic fallback so the pipeline can still proceed/demo even
        # if the manager's output wasn't parseable JSON.
        subtasks = [
            "Identify the likely customer pain points this product addresses.",
            "Identify 2-3 plausible competitor products and how this differs.",
            "Identify one likely objection or risk a skeptical buyer would raise.",
        ]
    return subtasks


async def run_subagent(subtask: str) -> str:
    system = (
        "You are a focused research subagent. You will be given exactly one "
        "subtask and nothing else. Respond ONLY to that subtask, in 2-4 "
        "sentences. You have no knowledge of any other subtask, of who else "
        "is working on this project, or of any overall synthesis that will "
        "happen later - just answer the subtask in front of you."
    )
    # The subagent gets product context (it needs SOME grounding to be
    # useful) plus its one subtask - and nothing about sibling subtasks or
    # the manager's own reasoning. That's the isolation property, and it's
    # enforced structurally here: this is its own query() call, so there is
    # no `messages` list a sibling's output could have leaked into even by
    # accident.
    user = f"Product: {PRODUCT_DESCRIPTION}\n\nYour subtask: {subtask}"
    return await call_claude(system, user)


async def manager_synthesize(goal: str, subtask_results: list[dict]) -> str:
    system = (
        "You are the manager who commissioned this research. Combine the "
        "results below into ONE coherent, short competitive launch brief "
        "(3-4 short paragraphs). Do not just list the results separately - "
        "synthesize them into a narrative."
    )
    results_block = "\n\n".join(
        f"Subtask: {r['subtask']}\nResult: {r['result']}" for r in subtask_results
    )
    user = f"Original goal: {goal}\n\nResearch results:\n\n{results_block}"
    return await call_claude(system, user)


async def run_manager_subagent_pipeline(goal: str) -> str:
    print("--- MANAGER: decomposing task ---")
    subtasks = await manager_decompose(goal)
    print(json.dumps(subtasks, indent=2))

    subtask_results = []
    for i, subtask in enumerate(subtasks, start=1):
        print(f"\n--- SUBAGENT {i} (isolated context) ---")
        print("Input (subtask only):", subtask)
        result = await run_subagent(subtask)
        print("Output:", result)
        subtask_results.append({"subtask": subtask, "result": result})

    print("\n--- MANAGER: synthesizing final brief ---")
    brief = await manager_synthesize(goal, subtask_results)
    return brief


async def main():
    goal = f"Produce a competitive launch brief for this product: {PRODUCT_DESCRIPTION}"
    final_brief = await run_manager_subagent_pipeline(goal)
    print("\n=== FINAL BRIEF ===")
    print(final_brief)
    # Total query() calls in this run: 1 (manager decompose) + 3 (subagents)
    # + 1 (manager synthesize) = 5, versus 1 call for a single-agent
    # baseline. Inspect the printed subagent inputs above and confirm none
    # of them contain text from a sibling subagent's output - that's the
    # isolation property this exercise is meant to make concrete, not just
    # assert.

    print(
        "\n=== ANSWER (reference discussion) ===\n"
        "For this specific task - one product, three short, low-effort "
        "subtasks - a single Claude call asked to cover all three angles "
        "directly would likely be simpler, cheaper (1 call vs 5), and just "
        "as good, since nothing here requires different tools, different "
        "specialized prompting, or genuinely independent parallel research; "
        "the manager/subagent overhead isn't earning its cost at this scale.\n"
        "The pattern would clearly pay off on a larger version of this task: "
        "e.g. 8-10 research angles instead of 3, where some angles need "
        "actual tool use (a subagent whose query() call is given a real "
        "web-search or docs-lookup tool to find real competitor names, vs. "
        "one that just reasons from general knowledge), where angles are "
        "independent enough to dispatch in parallel (e.g. with "
        "asyncio.gather over several run_subagent() calls) and meaningfully "
        "cut wall-clock latency, or where different angles benefit from "
        "different system prompts/model tiers (a cheap fast model for "
        "simple lookups, a stronger model for the risk/objection analysis "
        "that needs deeper reasoning). At that scale, context isolation "
        "also matters more concretely: 8-10 subtasks' worth of raw research "
        "transcripts would never fit usefully in one shared context, so "
        "isolating each subagent and only feeding the manager each one's "
        "distilled result is what makes the task tractable at all, not just "
        "tidier."
    )


if __name__ == "__main__":
    asyncio.run(main())
