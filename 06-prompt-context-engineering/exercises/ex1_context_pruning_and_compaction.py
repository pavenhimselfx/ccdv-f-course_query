"""
ex1_context_pruning_and_compaction.py — CCDV-F Module 06, Exercise 1

Skill: Context Engineering (3.8%)

WHAT YOU'RE BUILDING
---------------------
A simulated multi-turn agentic session. Each "turn" runs a fake tool that
returns a chunk of text (standing in for a file read, a search result, a big
API response — the kind of thing a real agent's tools return). Every tool
result gets appended to a running conversation history, the way it would in
a real tool-use loop (see Domain 1) where the *entire* history is resent on
every call because the API is stateless.

Left alone, this history only grows. Your job is to implement:

  1. estimate_size(...)   — a cheap proxy for "how many tokens is this,
                             roughly," used to decide when to act.
  2. prune_history(...)   — targeted truncation of old, oversized tool
                             results once they're no longer "recent."
  3. compact_history(...) — periodic wholesale summarization of an older
                             stretch of the transcript into one short
                             summary message.

Then you'll run a simulated session with pruning/compaction OFF and compare
its final context size against the SAME session with pruning/compaction ON,
to see the effect directly in characters (a stand-in for tokens).

NO API KEY REQUIRED. This exercise is entirely local simulation — it's about
the *mechanics* of context management, not about calling Claude. (Part 3 has
an optional bonus that uses the real `anthropic` client to produce a higher-
quality compaction summary if you have a key configured; it's clearly marked
optional and the exercise works fully without it.)

HOW TO KNOW YOU'VE SUCCEEDED
------------------------------
Running this file should print, for both the "unmanaged" and "managed"
versions of the same 8-turn session:
  - the running context size after each turn
  - the final context size
And the managed version's final size should be dramatically smaller than the
unmanaged version's, while still containing (in some form — full or
summarized) every turn's essential contribution.

Run it with:
    python ex1_context_pruning_and_compaction.py
"""

import random
import textwrap

random.seed(42)  # deterministic fake tool output for reproducible runs


# ---------------------------------------------------------------------------
# Fake tools: stand-ins for things a real agent's tools would return.
# ---------------------------------------------------------------------------

def fake_file_read_tool(step: int) -> str:
    """Simulate reading a moderately large file. Real tool outputs like this
    (a file, a search result page, a verbose API response) are exactly the
    kind of thing that bloats context if kept around verbatim forever."""
    lines = [f"line {i}: some source content for step {step} " + ("x" * 40) for i in range(60)]
    return "\n".join(lines)


def fake_search_tool(step: int) -> str:
    """Simulate a search-results tool returning several verbose hits."""
    hits = []
    for i in range(5):
        hits.append(
            f"Result {i} (step {step}): " + " ".join(random.choice(
                ["alpha", "beta", "gamma", "delta", "epsilon", "relevant", "context", "detail"]
            ) for _ in range(30))
        )
    return "\n".join(hits)


TOOLS = [fake_file_read_tool, fake_search_tool]


# ---------------------------------------------------------------------------
# The conversation history data structure.
#
# Each entry is a dict:
#   {"turn": int, "role": "user" | "assistant" | "tool_result",
#    "content": str, "pruned": bool}
#
# This is a simplified stand-in for a real Messages API history (which uses
# role="user"/"assistant" with tool_result content blocks nested inside user
# messages) — simplified here so the exercise can focus purely on size
# management logic rather than exact SDK message shapes.
# ---------------------------------------------------------------------------

def estimate_size(text: str) -> int:
    """
    TODO: Return a cheap size estimate for `text`.

    A real token count requires a tokenizer; for this exercise, character
    count is a fine stand-in (roughly 4 characters ~= 1 token for English
    text, but you don't even need to convert — just be consistent).

    Return: an int, the estimated size of `text`.
    """
    raise NotImplementedError


def total_history_size(history: list[dict]) -> int:
    """Already implemented for you: sums estimate_size() over every entry's
    content. You'll call this after each turn to track growth."""
    return sum(estimate_size(entry["content"]) for entry in history)


# ---------------------------------------------------------------------------
# Part 1: Pruning
# ---------------------------------------------------------------------------

def prune_history(history: list[dict], keep_recent_turns: int, max_len_for_old: int) -> list[dict]:
    """
    TODO: Implement targeted pruning of OLD tool results.

    Rule to implement:
      - Entries whose `turn` is within `keep_recent_turns` of the most
        recent turn in `history` are left completely untouched (an agent
        usually still needs the full detail of what just happened).
      - Entries older than that, with role == "tool_result" and content
        longer than `max_len_for_old`, get their `content` truncated to
        `max_len_for_old` characters with a marker appended, e.g.:
            content[:max_len_for_old] + f"... [{cut} chars pruned]"
        and their `pruned` flag set to True.
      - Entries that are already short enough, or aren't tool_result
        entries, are left alone.

    This should NOT remove entries from the list or reorder them — it only
    shrinks the `content` of qualifying old entries in place. Return the
    (mutated or new) list.

    Hint: `max(entry["turn"] for entry in history)` gives you the current
    turn number to compare against.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Part 2: Compaction
# ---------------------------------------------------------------------------

def naive_summarize(entries: list[dict]) -> str:
    """
    Already implemented for you: a crude, offline, non-LLM "summary" used as
    the default compaction summarizer so this exercise runs without an API
    key. It just records which turns/tools ran and how big they were —
    intentionally lossy, to make the pruning-vs-compaction tradeoff (section
    1.3 of the README) concrete: this is cheap but throws away real content.
    """
    parts = [f"turn {e['turn']} ({e['role']}, ~{estimate_size(e['content'])} chars)" for e in entries]
    return "[COMPACTED SUMMARY] Earlier turns condensed: " + "; ".join(parts)


def compact_history(history: list[dict], keep_recent_turns: int, summarizer=naive_summarize) -> list[dict]:
    """
    TODO: Implement periodic wholesale compaction.

    Rule to implement:
      1. Find the current turn number (the max `turn` in `history`).
      2. Split `history` into `old_entries` (turn <= current_turn -
         keep_recent_turns) and `recent_entries` (everything newer).
      3. If `old_entries` is empty, return `history` unchanged — nothing to
         compact yet.
      4. Otherwise, replace ALL of `old_entries` with a single new entry:
             {"turn": old_entries[-1]["turn"], "role": "summary",
              "content": summarizer(old_entries), "pruned": False}
         and return [that summary entry] + recent_entries.

    This is a coarser operation than prune_history: it can collapse MANY
    entries into ONE, regardless of their individual size, whereas pruning
    only shrinks individual oversized entries in place.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Part 3 (optional bonus): use the real Claude API to produce a better
# compaction summary than naive_summarize(). Only runs if ANTHROPIC_API_KEY
# is set; otherwise this function is simply not called.
# ---------------------------------------------------------------------------

def llm_summarize(entries: list[dict]) -> str:
    """
    OPTIONAL. TODO (bonus, only if you have an API key configured):
    Use `anthropic.Anthropic().messages.create(...)` to ask Claude to
    summarize the given entries' content into 2-3 sentences that preserve
    any concrete facts/values a later step of the "agent" might still need,
    and return that summary text.

    This is meant to make concrete that naive_summarize() above is a crude
    stand-in — a real compaction step usually asks the model itself (or a
    cheaper/faster model) to produce the summary, since it can judge what's
    actually still relevant far better than a fixed rule can.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Simulation driver — already implemented. Run the file to see it in action
# once you've filled in the TODOs above.
# ---------------------------------------------------------------------------

def run_unmanaged_session(num_turns: int) -> list[dict]:
    """Simulate a session that never prunes or compacts — pure accumulation,
    exactly what a naive tool-use loop does if you don't think about context
    management at all."""
    history: list[dict] = []
    print("\n=== UNMANAGED SESSION (no pruning, no compaction) ===")
    for turn in range(1, num_turns + 1):
        history.append({"turn": turn, "role": "user", "content": f"Step {turn}: please investigate X.", "pruned": False})
        tool_output = random.choice(TOOLS)(turn)
        history.append({"turn": turn, "role": "tool_result", "content": tool_output, "pruned": False})
        print(f"  after turn {turn}: total context size = {total_history_size(history)} chars")
    return history


def run_managed_session(num_turns: int, keep_recent_turns: int = 2, max_len_for_old: int = 120) -> list[dict]:
    """Simulate the SAME session, but prune old tool results after every
    turn and compact every 4 turns."""
    history: list[dict] = []
    print("\n=== MANAGED SESSION (pruning + periodic compaction) ===")
    for turn in range(1, num_turns + 1):
        history.append({"turn": turn, "role": "user", "content": f"Step {turn}: please investigate X.", "pruned": False})
        tool_output = random.choice(TOOLS)(turn)
        history.append({"turn": turn, "role": "tool_result", "content": tool_output, "pruned": False})

        history = prune_history(history, keep_recent_turns=keep_recent_turns, max_len_for_old=max_len_for_old)

        if turn % 4 == 0:
            history = compact_history(history, keep_recent_turns=keep_recent_turns)

        print(f"  after turn {turn}: total context size = {total_history_size(history)} chars "
              f"({len(history)} entries)")
    return history


def main() -> None:
    NUM_TURNS = 10

    unmanaged = run_unmanaged_session(NUM_TURNS)
    managed = run_managed_session(NUM_TURNS)

    print("\n=== COMPARISON ===")
    print(f"Unmanaged final size: {total_history_size(unmanaged)} chars across {len(unmanaged)} entries")
    print(f"Managed final size:   {total_history_size(managed)} chars across {len(managed)} entries")

    if total_history_size(unmanaged) > 0:
        reduction = 1 - (total_history_size(managed) / total_history_size(unmanaged))
        print(f"Reduction from managed context strategy: {reduction:.0%}")

    print(textwrap.dedent("""
        REFLECTION (fill this in yourself once your implementation runs):
          - Roughly what fraction of context size did pruning + compaction save?
          - Which technique (pruning vs. compaction) contributed more to the
            reduction in THIS simulation, and why does that make sense given
            how each one works?
          - naive_summarize() is deliberately lossy. Name one concrete piece
            of information from a tool_result that it throws away, and describe
            a situation later in a session where losing that detail could hurt
            the agent.
    """))


if __name__ == "__main__":
    main()
