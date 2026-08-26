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


MODEL = "claude-sonnet-4-5"  # verify current model name/availability at docs.claude.com

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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    return response.content[0].text


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
"""


if __name__ == "__main__":
    main()
