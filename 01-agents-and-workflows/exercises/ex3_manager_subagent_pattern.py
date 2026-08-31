"""
Exercise 3: Manager / Subagent Pattern
========================================
Domain 1 (Agents and Workflows) - Skills: Agent Architecture (4.5%) and
Agent Patterns and Frameworks (4.9%)

RUNS FREE ON A TEAM/ENTERPRISE (OR PRO/MAX) SUBSCRIPTION
-----------------------------------------------------------
Like Exercise 1, this is built on the **Claude Agent SDK** (`claude-agent-sdk`)
rather than the raw `anthropic` Messages API package, so it authenticates via
CLAUDE_CODE_OAUTH_TOKEN against your Claude.ai subscription instead of a
metered Console API key. See `00-setup/README.md` section 1 if you haven't
run `claude setup-token` yet. As with Exercise 1, treat the exact Agent SDK
call shapes below as "verify against code.claude.com if this SDK has moved
since this was written."

THE TASK
--------
Simulate a manager/supervisor multi-agent pattern for the task: "produce a
short competitive-launch brief for a new product" given three independent
research angles:
  1. Likely customer pain points the product addresses
  2. Two or three plausible competitor products and how they differ
  3. A risk/objection a skeptical buyer might raise

Structure:

  MANAGER call:
    Given the overall goal, decompose it into the three subtasks above (or
    have Claude generate its own decomposition - see TODO). Output should
    be a small structured list of subtask descriptions.

  SUBAGENT calls (one per subtask):
    For EACH subtask, make a SEPARATE, ISOLATED `query()` call to Claude
    that receives ONLY that subtask's description - not the other subtasks,
    not the manager's reasoning, not any other subagent's output. Each
    subagent returns a short, focused result (2-4 sentences).

    *** WHY ISOLATED CONTEXT? ***
    If all three subagents shared one growing conversation, subagent 2's
    context would include subagent 1's full output, subagent 3's would
    include both - and the more of that unrelated material sits in context,
    the more it can bias, distract, or "pollute" reasoning that has nothing
    to do with it (this is sometimes called context drift/pollution). It
    also means growing latency/cost per subagent and makes it much harder
    to reason about why a given subagent produced what it produced, since
    its input is no longer just its own subtask. Giving each subagent a
    clean slate - just its own subtask - keeps its reasoning focused,
    keeps subagents independently parallelizable, and keeps the manager's
    synthesis step the ONLY place where information from different subtasks
    actually mixes, which is a deliberate, inspectable point in the
    pipeline rather than an accident of shared context.

    This is precisely why each subagent below is its OWN, independent
    `query()` call rather than one shared conversation with three turns:
    a fresh `query()` call starts with empty context every time - you never
    have to remember to clear anything, isolation is just what happens by
    default when you make a new call instead of continuing an old one.

  MANAGER SYNTHESIS call:
    A final Claude call that receives the ORIGINAL goal plus all three
    subagent results (not their intermediate reasoning, just their final
    outputs) and produces one coherent launch brief combining them.

WHAT YOU SHOULD OBSERVE / HOW TO KNOW YOU SUCCEEDED
----------------------------------------------------
- Print each subagent's isolated input and output separately. Confirm by
  inspection that subagent 2's prompt contains NO text from subagent 1's
  output, and vice versa - that isolation is the whole point of the
  exercise, so verify it, don't just assume your code does it. (This is
  easy to verify here precisely because each subagent is its own `query()`
  call built from a prompt string you construct fresh each time - there's
  no shared `messages` list any subagent could accidentally see into.)
- The final brief should read as a coherent synthesis, not just three
  results pasted end to end - that synthesis step is where the manager
  earns its keep.
- Time (or just count `query()` calls for) this pattern vs. a single "do
  everything in one Claude call" baseline. For a task this small, a single
  call may well be simpler AND cheaper - that's expected and important to
  notice. Answer the closing prompt about when the extra complexity here
  would actually pay for itself at larger scale.

NO CREDENTIALS SET UP YET? Write out, by hand, what you'd expect each of the
five calls (manager decomposition, subagent 1, subagent 2, subagent 3,
manager synthesis) to receive as input and roughly produce as output, then
write the final synthesized brief yourself as if you were the manager.
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
    """
    TODO(shared helper): One isolated, single-turn Claude call. Build
    `ClaudeAgentOptions(system_prompt=system)` and run:

        chunks = []
        async for message in query(prompt=user, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)
        return "".join(chunks).strip()

    No shared message history is threaded through here on purpose - every
    call to this function starts a brand-new `query()` call with a fresh
    context, which is exactly what we want for the manager AND for each
    subagent below: isolation is achieved simply by never reusing a prior
    call's context, not by any extra "clear the context" step.
    """
    options = ClaudeAgentOptions(system_prompt=system)
    chunks = []
    async for message in query(prompt=user, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks).strip()


async def manager_decompose(goal: str) -> list[str]:
    """
    TODO: Call `call_claude` with a system prompt establishing it as a
    project manager decomposing a research task, and a user prompt
    containing `goal`. Ask it to return a JSON array of exactly 3 short
    subtask descriptions (strings), covering: customer pain points,
    competitor landscape, and likely buyer objections/risks.

    Parse the JSON array out of the response and return it as a
    list[str]. (Ask explicitly for "ONLY a JSON array of 3 strings, no
    other text" to make parsing reliable.)
    """
    system = (
        "You are a project manager decomposing a research task into "
        "focused subtasks for independent research subagents."
    )
    user = (
        f"Goal: {goal}\n\n"
        "Decompose this into exactly 3 short subtask descriptions covering:\n"
        "1. Likely customer pain points the product addresses\n"
        "2. Two or three plausible competitor products and how they differ\n"
        "3. A risk/objection a skeptical buyer might raise\n\n"
        "Respond with ONLY a JSON array of exactly 3 strings, no other text."
    )
    response = await call_claude(system, user)
    return json.loads(response)


async def run_subagent(subtask: str) -> str:
    """
    TODO: Call `call_claude` with:
      - system: something like "You are a focused research subagent. You
        will be given exactly one subtask. Respond ONLY to that subtask in
        2-4 sentences. You have no knowledge of any other subtask or of the
        overall project beyond what's stated here."
      - user: just `subtask` plus, if useful, PRODUCT_DESCRIPTION for
        context (the subtask needs SOME product context to be useful - but
        note it still gets ZERO information about sibling subtasks or the
        manager's own reasoning, which is the isolation property that
        matters - this call is a brand new `query()` invocation with no
        connection to the manager's or any sibling subagent's call).

    Return the subagent's text response.
    """
    system = (
        "You are a focused research subagent. You will be given exactly "
        "one subtask. Respond ONLY to that subtask in 2-4 sentences. You "
        "have no knowledge of any other subtask or of the overall project "
        "beyond what's stated here."
    )
    user = f"Product: {PRODUCT_DESCRIPTION}\n\nSubtask: {subtask}"
    return await call_claude(system, user)


async def manager_synthesize(goal: str, subtask_results: list[dict]) -> str:
    """
    TODO: Call `call_claude` with a system prompt establishing it as the
    manager writing a final brief, and a user prompt containing the
    original `goal` plus all of the subagent results (subtask_results is a
    list of {"subtask": ..., "result": ...} dicts - format them clearly in
    the prompt). Ask for one coherent short launch brief (a few short
    paragraphs) that draws on all three results.

    Return the final brief text.
    """
    system = (
        "You are the manager writing a final competitive launch brief by "
        "synthesizing independent research results into one coherent brief."
    )
    results_block = "\n\n".join(
        f"Subtask: {item['subtask']}\nResult: {item['result']}"
        for item in subtask_results
    )
    user = (
        f"Goal: {goal}\n\n"
        f"Research results from independent subagents:\n\n{results_block}\n\n"
        "Write one coherent short launch brief (a few short paragraphs) "
        "that draws on all three results."
    )
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
    try:
        final_brief = await run_manager_subagent_pipeline(goal)
        print("\n=== FINAL BRIEF ===")
        print(final_brief)
    except NotImplementedError as e:
        print(f"(not implemented yet: {e})")

    print(
        "\n=== ANSWER (fill in, 3-5 sentences) ===\n"
        "For a task this small (one product, three short subtasks), is the "
        "manager/subagent pattern's extra complexity (5 query() calls, "
        "isolated contexts, a synthesis step) actually worth it compared to "
        "one single Claude call asked to cover all three angles directly? "
        "Then describe a LARGER version of this task (e.g., many more "
        "research angles, or angles requiring different tools/specialized "
        "prompts, or angles independent enough to run in parallel for "
        "latency) where the pattern's benefits - context isolation, "
        "parallelism, specialization - would clearly outweigh its "
        "coordination overhead."
    )


if __name__ == "__main__":
    asyncio.run(main())
