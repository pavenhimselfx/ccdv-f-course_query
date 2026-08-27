"""
SOLUTION — ex1_context_pruning_and_compaction.py — CCDV-F Module 06

Reference implementation with inline explanations. Compare against your own
attempt in exercises/ex1_context_pruning_and_compaction.py after a genuine
attempt of your own. See that file's docstring for full exercise context.
"""

import os
import random
import textwrap

random.seed(42)


# ---------------------------------------------------------------------------
# Fake tools (identical to the exercise file -- these represent the kind of
# large, variable tool output a real agent's tools produce).
# ---------------------------------------------------------------------------

def fake_file_read_tool(step: int) -> str:
    lines = [f"line {i}: some source content for step {step} " + ("x" * 40) for i in range(60)]
    return "\n".join(lines)


def fake_search_tool(step: int) -> str:
    hits = []
    for i in range(5):
        hits.append(
            f"Result {i} (step {step}): " + " ".join(random.choice(
                ["alpha", "beta", "gamma", "delta", "epsilon", "relevant", "context", "detail"]
            ) for _ in range(30))
        )
    return "\n".join(hits)


TOOLS = [fake_file_read_tool, fake_search_tool]


def estimate_size(text: str) -> int:
    """
    Character count as a token-count proxy. A real system would use the
    model's actual tokenizer (or the API's token-counting endpoint) for
    precision, but for *deciding when to prune/compact* -- a threshold
    check, not a billing calculation -- a cheap proxy like this is exactly
    what you want: fast, no extra dependency, good enough to trigger the
    right behavior at the right rough scale.
    """
    return len(text)


def total_history_size(history: list[dict]) -> int:
    return sum(estimate_size(entry["content"]) for entry in history)


# ---------------------------------------------------------------------------
# Part 1: Pruning
# ---------------------------------------------------------------------------

def prune_history(history: list[dict], keep_recent_turns: int, max_len_for_old: int) -> list[dict]:
    """
    Targeted, per-entry truncation. Note what this function does NOT do:
    it never removes an entry from the list, never touches "recent" turns
    (the agent may still need their full detail), and never touches
    non-tool_result entries (a user instruction is usually short and
    meaningful regardless of age -- there's rarely a reason to prune it).
    That narrowness is the point: pruning is a scalpel, not a hard reset.
    """
    if not history:
        return history

    current_turn = max(entry["turn"] for entry in history)

    for entry in history:
        is_old = (current_turn - entry["turn"]) >= keep_recent_turns
        if not is_old:
            continue
        if entry["role"] != "tool_result":
            continue
        if len(entry["content"]) <= max_len_for_old:
            continue  # already short enough, nothing to do

        cut = len(entry["content"]) - max_len_for_old
        entry["content"] = entry["content"][:max_len_for_old] + f"... [{cut} chars pruned]"
        entry["pruned"] = True

    return history


# ---------------------------------------------------------------------------
# Part 2: Compaction
# ---------------------------------------------------------------------------

def naive_summarize(entries: list[dict]) -> str:
    parts = [f"turn {e['turn']} ({e['role']}, ~{estimate_size(e['content'])} chars)" for e in entries]
    return "[COMPACTED SUMMARY] Earlier turns condensed: " + "; ".join(parts)


def compact_history(history: list[dict], keep_recent_turns: int, summarizer=naive_summarize) -> list[dict]:
    """
    Wholesale replacement of an older SPAN of the transcript with one
    summary entry. Note the key structural difference from prune_history:
    this can collapse many entries (each of whatever size) down to exactly
    one entry, whereas pruning only ever shrinks individual entries without
    changing how many there are. That's what makes compaction the right
    tool for controlling entry *count* and long-run growth, while pruning
    is the right tool for controlling any single entry's size.
    """
    if not history:
        return history

    current_turn = max(entry["turn"] for entry in history)
    cutoff = current_turn - keep_recent_turns

    old_entries = [e for e in history if e["turn"] <= cutoff]
    recent_entries = [e for e in history if e["turn"] > cutoff]

    if not old_entries:
        return history  # nothing old enough yet -- no-op, as specified

    summary_entry = {
        "turn": old_entries[-1]["turn"],
        "role": "summary",
        "content": summarizer(old_entries),
        "pruned": False,
    }
    return [summary_entry] + recent_entries


# ---------------------------------------------------------------------------
# Part 3 (optional bonus): LLM-based summarization.
# ---------------------------------------------------------------------------

def llm_summarize(entries: list[dict]) -> str:
    """
    Uses the real Claude API to produce a better summary than the naive
    rule-based one above. This is what a production compaction step
    actually tends to do: ask a model (often a smaller/cheaper one, since
    summarization is a comparatively easy task) to condense a stretch of
    transcript into a few sentences that keep whatever a later step might
    still need -- concrete facts, decisions, open questions -- and drop the
    rest. Falls back to naive_summarize() if no API key is configured, so
    the rest of the pipeline still works without one.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return naive_summarize(entries)

    try:
        import anthropic
    except ImportError:
        return naive_summarize(entries)

    combined = "\n---\n".join(f"(turn {e['turn']}, {e['role']}): {e['content']}" for e in entries)
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5",  # cheap/fast model -- summarization doesn't need a frontier model
        max_tokens=150,
        system=(
            "You compact agent transcripts. Given several old turns of an "
            "agent's tool-use history, write a 2-3 sentence summary that "
            "preserves any concrete facts, decisions, or values a later "
            "step of the agent might still need. Omit raw data that is no "
            "longer relevant. Output only the summary, no preamble."
        ),
        messages=[{"role": "user", "content": combined}],
    )
    return "[COMPACTED SUMMARY, LLM] " + response.content[0].text


# ---------------------------------------------------------------------------
# Simulation driver
# ---------------------------------------------------------------------------

def run_unmanaged_session(num_turns: int) -> list[dict]:
    history: list[dict] = []
    print("\n=== UNMANAGED SESSION (no pruning, no compaction) ===")
    for turn in range(1, num_turns + 1):
        history.append({"turn": turn, "role": "user", "content": f"Step {turn}: please investigate X.", "pruned": False})
        tool_output = random.choice(TOOLS)(turn)
        history.append({"turn": turn, "role": "tool_result", "content": tool_output, "pruned": False})
        print(f"  after turn {turn}: total context size = {total_history_size(history)} chars")
    return history


def run_managed_session(num_turns: int, keep_recent_turns: int = 2, max_len_for_old: int = 120) -> list[dict]:
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
        REFLECTION (reference answers -- yours may reasonably differ in the
        exact numbers, but should point the same direction):

          - Reduction is typically large -- often 70-90%+ in this simulation
            -- because pruning caps every old tool_result at max_len_for_old
            (120 chars, vs. raw outputs of 1000+ chars), and compaction on
            top of that collapses whole groups of already-pruned entries
            into a single short summary entry every 4 turns.

          - Compaction usually contributes more to the FINAL number in a
            long-running session, because it also reduces entry *count*
            (which matters for per-message overhead and for how much of the
            transcript the model has to read through), whereas pruning caps
            size per-entry but leaves the entry count growing. In a short
            session, pruning alone already captures most of the benefit
            since compaction hasn't triggered (turn % 4 == 0) very often
            yet.

          - naive_summarize() throws away every concrete piece of tool
            output content -- it only records metadata (turn number, role,
            size). If turn 3's tool_result contained a specific value (a
            file path, an error code, a specific search hit) that turn 9's
            reasoning needs to reference, naive_summarize's compacted
            version can't provide it -- the agent would have to re-run the
            tool, or the answer would be wrong/missing. This is exactly why
            llm_summarize() (or any real summarizer) needs to be judged on
            whether it preserves the *specific facts that turn out to
            matter later*, not just on how much shorter it makes the
            transcript.
    """))


if __name__ == "__main__":
    main()
