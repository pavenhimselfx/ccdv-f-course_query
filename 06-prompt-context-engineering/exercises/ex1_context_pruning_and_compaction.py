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

import os
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
    return len(text)


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
    if not history:
        return history

    current_turn = max(entry["turn"] for entry in history)
    for entry in history:
        if entry["turn"] > current_turn - keep_recent_turns:
            continue  # recent -- leave untouched
        if entry["role"] != "tool_result":
            continue
        content = entry["content"]
        if len(content) <= max_len_for_old:
            continue
        cut = len(content) - max_len_for_old
        entry["content"] = content[:max_len_for_old] + f"... [{cut} chars pruned]"
        entry["pruned"] = True

    return history


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
    if not history:
        return history

    current_turn = max(entry["turn"] for entry in history)
    threshold = current_turn - keep_recent_turns
    old_entries = [e for e in history if e["turn"] <= threshold]
    recent_entries = [e for e in history if e["turn"] > threshold]

    if not old_entries:
        return history

    summary_entry = {
        "turn": old_entries[-1]["turn"],
        "role": "summary",
        "content": summarizer(old_entries),
        "pruned": False,
    }
    return [summary_entry] + recent_entries


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
    import anthropic

    client = anthropic.Anthropic()
    transcript = "\n\n".join(
        f"Turn {e['turn']} ({e['role']}):\n{e['content']}" for e in entries
    )
    prompt = (
        "Summarize the following agent transcript turns into 2-3 sentences. "
        "Preserve any concrete facts, values, or identifiers a later step of "
        "the agent might still need; drop verbose filler and repeated boilerplate.\n\n"
        f"{transcript}"
    )
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    # Not response.content[0].text -- see Domain 5's exercises: a thinking
    # block can precede the text block, so filter by type rather than
    # assume position.
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


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

    # Optional bonus (Part 3): only runs with a real key, since nothing in
    # the core exercise depends on it. Demonstrates naive_summarize()'s
    # crude, offline summary vs. an LLM-produced one on the SAME old turns
    # (the first 4 turns of the unmanaged session, still full/undegraded),
    # so the quality difference is directly comparable.
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("\n=== BONUS: naive_summarize() vs. llm_summarize() on the same turns ===")
        sample_old_entries = unmanaged[:8]  # turns 1-4 (2 entries/turn), before any pruning/compaction touched them
        print("naive_summarize():\n ", naive_summarize(sample_old_entries))
        print("\nllm_summarize():\n ", llm_summarize(sample_old_entries))
    else:
        print("\n(Set ANTHROPIC_API_KEY to also see the optional llm_summarize() bonus comparison.)")

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

    ANSWER (from a real run of this file):
      Reduction: 85% (unmanaged 45,101 chars / 20 entries -> managed 6,681
      chars / 9 entries over the same 10-turn session).

      Pruning did most of the character-count reduction; compaction's real
      contribution here was bounding entry COUNT, not raw size. Traced the
      first compaction (turn 4) directly: by then, pruning had already
      shrunk turns 1-2's oversized tool_results down to ~141/143 chars each
      (from thousands of chars originally) the moment they aged out of the
      keep_recent_turns=2 window. Compaction then collapsed those 4
      ALREADY-PRUNED entries into one 163-char summary -- a real but small
      saving (342 -> 163 chars, ~179 chars), because there wasn't much left
      to save; pruning got there first. Meanwhile turns 3-4 (still "recent,"
      untouched by either mechanism) accounted for 5,958 of the 6,179 total
      chars at that point -- the dominant cost at any moment is always
      whatever's currently in the recent window, which neither technique
      touches by design. This makes sense given how each works: pruning
      acts immediately and repeatedly on individual oversized entries the
      moment they age out, so it's already capped the big offenders by the
      time compaction gets a turn; compaction's distinct value is that it
      caps the NUMBER of old entries (4 -> 1 here), which matters over an
      arbitrarily long session where pruned-but-still-separate entries
      would otherwise keep accumulating one per turn forever, even at a
      small, bounded size each.

      naive_summarize() keeps only turn number, role, and character count
      -- e.g. "turn 1 (tool_result, ~141 chars)" -- and discards 100% of
      the actual content, including whatever survived pruning's 120-char
      truncation. Concretely: if turn 1's tool_result had contained a
      specific value the agent needs later (a file path, a config key, an
      ID returned by a search), that value is gone completely once
      compaction runs over it -- pruning at least keeps the first
      max_len_for_old characters, but compaction's naive summary keeps
      none. If a user asked at turn 8 "what was that value we found back in
      turn 1?", the agent has no way to answer from context anymore; it
      would have to guess or hallucinate a plausible-sounding but
      unverifiable answer rather than admit the detail was compacted away
      -- exactly the failure mode llm_summarize() (Part 3) exists to
      reduce, by asking a model to judge what's worth keeping instead of
      discarding all content unconditionally.

      BONUS, from a real run with llm_summarize(): the actual result
      refined this prediction rather than confirming it outright. The fake
      tool data here has NO real facts embedded (file reads are literally
      "some source content ... xxxx"; search hits are random alpha/beta/
      gamma-style words) -- so there was no hidden value for llm_summarize
      to "recover." What it did instead was still strictly more useful
      than naive_summarize in a different way: it named WHICH TOOL ran and
      the SHAPE of what it returned ("retrieving source content in steps
      1, 2, and 4 (60 lines each)" vs. "structured results in step 3
      containing terms like ... alpha, beta, gamma"), where naive_summarize
      only ever records generic tool_result/~N chars with no hint of what
      kind of data that was. It also explicitly said "no concrete facts,
      values, or identifiers were provided to preserve" instead of
      inventing a plausible-sounding fake one -- the correct, honest
      behavior when there's genuinely nothing worth keeping. So the
      real-world value of llm_summarize() isn't only "recovers facts a
      fixed rule would lose" (true when facts exist) -- it's also
      "preserves semantic/structural context a fixed rule can't represent
      at all, and doesn't fabricate specifics when there's nothing to
      report," which matters just as much for an agent trying to
      understand what already happened in a session.
    """))


if __name__ == "__main__":
    main()
