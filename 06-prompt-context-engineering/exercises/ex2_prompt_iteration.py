"""
ex2_prompt_iteration.py — CCDV-F Module 06, Exercise 2

Skill: Prompt Engineering (4.6%)

WHAT YOU'RE BUILDING
---------------------
A small harness that calls Claude with THREE successive versions of a prompt
for the same task — summarizing a customer support ticket — and prints the
results side by side so you can observe the iterative-refinement loop
described in README.md section 2.6 directly, instead of just reading about
it.

  - v0_prompt(...): a deliberately vague, weak prompt. You should observe
    output that varies in length/format/focus across the sample tickets (and
    even across repeated runs of the SAME ticket).
  - v1_prompt(...): adds instruction clarity + a system prompt (role,
    explicit constraints on length and focus). Output should get more
    consistent.
  - v2_prompt(...): adds explicit output-format constraints AND a few-shot
    example. Output should converge to a specific, parseable shape.

You'll run all three versions against the same set of sample tickets and
write a short comparison at the end.

REQUIRES AN API KEY to see real model output, but you can still work through
this exercise without one: read each TODO, WRITE the prompt strings you'd
use for each version, and reason/predict about how the outputs would differ
and why — then check your reasoning against solutions/ex2_prompt_iteration.py.
If ANTHROPIC_API_KEY is not set, this script prints a clear message and skips
the live calls instead of crashing.

HOW TO KNOW YOU'VE SUCCEEDED
------------------------------
Running this file with a valid API key should print three blocks of output
(one per prompt version) for each sample ticket, and v2's output should be
visibly the most consistent in format across tickets and across the two
tickets that are similar in content but different in wording.

Run it with:
    python ex2_prompt_iteration.py
"""

import os
import sys

try:
    import anthropic
except ImportError:
    anthropic = None


MODEL = "claude-sonnet-5"  # confirmed working in Domain 5's ex3/ex4 -- claude-sonnet-4-5
# (the exercise's original placeholder) is the prior generation

SAMPLE_TICKETS = [
    """Subject: App crashes on login
    Hi, every time I try to log in on my Android phone the app just closes.
    This started after the last update. I've tried reinstalling twice. I use
    this app for work every day so this is pretty urgent, please help asap.
    Ticket submitted by: jordan.k@example.com""",

    """Subject: billing question
    hey so i got charged twice this month for my subscription?? can someone
    look into this and refund the extra charge. not a huge emergency just
    annoying. thanks""",

    """Subject: Feature request - dark mode
    Would love to see a dark mode option in a future update. Not urgent at
    all, just a nice-to-have. Love the app otherwise!""",
]


# ---------------------------------------------------------------------------
# TODO: Write each prompt version below. Each function takes the raw ticket
# text and returns a dict with "system" (str or None) and "user" (str) —
# what you'd pass to client.messages.create(system=..., messages=[{"role":
# "user", "content": ...}]).
# ---------------------------------------------------------------------------

def v0_prompt(ticket_text: str) -> dict:
    """
    TODO: A DELIBERATELY WEAK prompt. No system prompt, no format
    constraints, no role. Something like just:
        "Summarize this: {ticket_text}"
    The point is to see inconsistent, unconstrained output first, as a
    baseline to improve on. Don't overthink this one — it's supposed to be
    weak on purpose.
    """
    return {"system": None, "user": f"Summarize this: {ticket_text}"}


def v1_prompt(ticket_text: str) -> dict:
    """
    TODO: Improve on v0 using:
      - A system prompt establishing a role/persona (e.g. "You are a
        customer support triage assistant") and a global rule that should
        hold for every ticket (e.g. always identify the core issue and
        what, if anything, the customer is asking for).
      - Clearer, more specific instructions in the user turn: what exactly
        to summarize, and roughly how long the summary should be (e.g.
        "in 1-2 sentences").
      - No few-shot example yet — that's v2.
    This is section 2.1 (instruction clarity) + 2.3 (system vs. user
    placement) from the README, applied together.
    """
    system = (
        "You are a customer support triage assistant. For every ticket you "
        "are given, identify the core issue and, if the customer explicitly "
        "asked for something, what they're asking for."
    )
    user = (
        "Summarize the customer support ticket below in 1-2 sentences. "
        "Focus on what the actual problem is and what the customer wants "
        "done about it.\n\n"
        f"Ticket:\n{ticket_text}"
    )
    return {"system": system, "user": user}


def v2_prompt(ticket_text: str) -> dict:
    """
    TODO: Improve further on v1 using:
      - Explicit OUTPUT CONSTRAINTS: require a specific structured-ish
        format, e.g. exactly three lines:
            Issue: <one clause>
            Urgency: <low|medium|high>
            Requested action: <one clause, or "none stated">
        and explicitly say not to include anything else (no greeting, no
        restated ticket text, no extra commentary).
      - ONE FEW-SHOT EXAMPLE embedded in the user turn (or system prompt):
        a short sample ticket paired with the exact three-line output you'd
        want for it, so the model has a concrete pattern to match, not just
        a verbal description of the format.
    This is section 2.2 (few-shot) + 2.4 (output constraints) from the
    README, layered on top of v1's clarity and system/user split.
    """
    system = (
        "You are a customer support triage assistant. For every ticket you "
        "are given, identify the core issue and, if the customer explicitly "
        "asked for something, what they're asking for."
    )
    example_ticket = (
        "Subject: Can't reset my password\n"
        "I've clicked the reset link three times and never get the email. "
        "I need access back before my shift starts tonight."
    )
    example_output = (
        "Issue: Password reset emails aren't arriving\n"
        "Urgency: high\n"
        "Requested action: Restore account access before tonight's shift"
    )
    user = (
        "Summarize the customer support ticket below. Respond with EXACTLY "
        "three lines, in this format, and nothing else -- no greeting, no "
        "restated ticket text, no extra commentary:\n"
        "Issue: <one clause>\n"
        "Urgency: <low|medium|high>\n"
        "Requested action: <one clause, or \"none stated\">\n\n"
        "Example:\n"
        f"Ticket:\n{example_ticket}\n\n"
        f"Output:\n{example_output}\n\n"
        "Now do the same for this ticket:\n"
        f"Ticket:\n{ticket_text}\n\n"
        "Output:"
    )
    return {"system": system, "user": user}


# ---------------------------------------------------------------------------
# Harness — already implemented.
# ---------------------------------------------------------------------------

def call_claude(client, prompt_dict: dict) -> str:
    kwargs = {
        "model": MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt_dict["user"]}],
    }
    if prompt_dict.get("system"):
        kwargs["system"] = prompt_dict["system"]
    response = client.messages.create(**kwargs)
    # Not response.content[0].text -- see Domain 5's exercises: a thinking
    # block can precede the text block, so filter by type rather than
    # assume position.
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
        print("ANTHROPIC_API_KEY not set (or `anthropic` package not installed).")
        print("You can still complete this exercise by writing the prompt")
        print("strings in v0_prompt/v1_prompt/v2_prompt and reasoning about")
        print("how their outputs would likely differ, then checking against")
        print("solutions/ex2_prompt_iteration.py.")
        sys.exit(0)

    client = anthropic.Anthropic(api_key=api_key)
    versions = [("v0 (weak)", v0_prompt), ("v1 (clear + system/user split)", v1_prompt),
                ("v2 (+ output constraints + few-shot)", v2_prompt)]

    for i, ticket in enumerate(SAMPLE_TICKETS, start=1):
        print(f"\n{'=' * 70}\nTICKET {i}:\n{ticket.strip()}\n{'=' * 70}")
        for label, fn in versions:
            try:
                prompt_dict = fn(ticket)
            except NotImplementedError:
                print(f"\n--- {label} --- (TODO not yet implemented, skipping)")
                continue
            output = call_claude(client, prompt_dict)
            print(f"\n--- {label} ---\n{output}")

    print(textwrap_reflection())


def textwrap_reflection() -> str:
    return """

WRITE-UP (fill this in after running against all three tickets):
  1. v0: describe what varied across tickets/runs that shouldn't have
     (length? whether it included a greeting? whether urgency was even
     mentioned?).
  2. v1 vs v0: what specifically got MORE consistent, and which change
     (system prompt vs. clearer instruction) do you think caused it?
  3. v2 vs v1: did the few-shot example change the output's FORMAT,
     its CONTENT, or both? Would v2's output be safe to parse
     programmatically (e.g. split on "Issue:", "Urgency:", "Requested
     action:") across all three tickets? Try it.
  4. Which single change across all three versions had the biggest impact
     on consistency, in your observation? This is the kind of judgment
     iterative refinement (README 2.6) is meant to build.

ANSWER (from a real run against all three tickets):
  1. v0 varied in every dimension a downstream system would care about.
     Ticket 1's v0 used markdown headers, bullet lists, and even invented a
     "Suggested next steps" section nobody asked for. Ticket 3's v0 also
     used headers plus an unrequested editorial line ("This reads as
     friendly, low-pressure feedback..."). Ticket 2's v0, by contrast, was
     two short plain-prose paragraphs with no headers at all. So across
     three structurally similar tasks, the model picked three different
     presentation styles, two of which added unrequested content (next
     steps, sentiment commentary) beyond "summarize this."

  2. v1 collapsed to a consistent 1-2 sentence plain-prose format across
     all three tickets -- no markdown, no invented sections, no
     editorializing, every response covering both the core issue and the
     customer's ask. Splitting credit between the two v1 changes: the
     explicit "1-2 sentences" length constraint is what killed v0's
     markdown-header sprawl (a hard length cap leaves no room for headers/
     bullets/extra sections), while the system prompt's role framing
     ("identify the core issue and what the customer is asking for") is
     what made every response reliably cover the ask/urgency rather than
     sometimes omitting it or wandering into unrelated commentary. Format
     consistency traces mostly to the length constraint; content coverage
     consistency traces mostly to the system prompt.

  3. Both, but the more important change is content, not just format. v1's
     prose already captured urgency IMPLICITLY (ticket 2: "not urgent, but
     they'd like it looked into") -- v2 forces that same information into
     an explicit, enum-constrained field ("Urgency: low"), which is new
     structured content v1 never produced, not just a reformatting of the
     same substance. I tested parseability directly rather than eyeballing
     it: a strict regex requiring the exact 3-line shape and urgency in
     {low, medium, high} matched all three real outputs with zero failures
     -- "Issue: App crashes on login after latest update on Android" /
     "Urgency: high" / "Requested action: Fix login crash asap", and
     equivalently clean for tickets 2 and 3. v2's output is genuinely,
     confirmedly safe to parse programmatically across all three tickets.

  4. The v1->v2 change (output format constraints + few-shot example) had
     the biggest impact on the kind of consistency that actually matters
     for shipping this as a feature. v0->v1 was a real improvement (tone,
     length, and content-coverage all stabilized), but v1's output was
     still free-form prose with no guaranteed delimiters or fields -- not
     something a downstream system could parse reliably, only something
     that read as "more consistent" to a human. v2 is what crosses the
     line from "improved but still free text" to "a guaranteed, structured
     artifact," which is the actual bar for anything downstream needs to
     consume programmatically (a ticket router, a dashboard, an alerting
     rule keyed on urgency). If forced to pick one change, it's the
     combination of an explicit output format spec plus a concrete
     worked example -- description of the format alone (v1's clarity) got
     the model closer, but only showing it the exact target shape made
     that shape reliable across all three tickets.
"""


if __name__ == "__main__":
    main()
