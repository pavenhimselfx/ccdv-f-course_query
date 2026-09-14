"""
ex3_secrets_and_key_hygiene.py — CCDV-F Module 07 (Security and Safety)

SKILL: Identity, Secrets, and Key Management — managing secrets, credentials,
and API keys across development and production environments.

SCENARIO
--------
Below is a deliberately BAD starting snippet (`bad_get_client()`) with an API
key hardcoded as a string literal, plus a couple of other common
key-hygiene mistakes sprinkled in for you to spot and fix. Your job is to:

  1. Read `bad_get_client()` and, in the TODO comment above it, list every
     mistake you can find (there are at least three).
  2. Implement `good_get_client()`: a refactored version that loads the key
     from an environment variable (optionally via a local .env file, using
     python-dotenv — same pattern as 00-setup/verify_setup.py), fails with a
     clear error message if the key is missing, and never logs or prints the
     key itself.
  3. Fill in the KEY_MANAGEMENT_CHECKLIST comment block with the best
     practices from the README (rotation, least privilege / scoped keys per
     environment, never logging secrets, not hardcoding, etc).

This exercise needs no live API call to complete — steps 1-3 are all about
the *code and reasoning*, not about actually talking to Claude. If you do
have an ANTHROPIC_API_KEY set, `run_smoke_test()` at the bottom will use
`good_get_client()` to confirm it can actually authenticate.

Run with:
    python ex3_secrets_and_key_hygiene.py
"""

import os


# ---------------------------------------------------------------------------
# BAD EXAMPLE — do not copy this pattern. Read it, then list every mistake
# you can find in the TODO comment below before moving on.
# ---------------------------------------------------------------------------

def bad_get_client():
    """DO NOT DO THIS. Kept here only as a worked "what's wrong" example."""
    import anthropic

    # Mistake: API key hardcoded directly in source code.
    api_key = "sk-ant-api03-THIS-IS-A-FAKE-EXAMPLE-KEY-DO-NOT-USE-1234567890"

    # Mistake: the same literal key would be used for dev, staging, and
    # prod alike if this code were deployed as-is — no per-environment
    # scoping at all.

    print(f"Connecting to Anthropic with key: {api_key}")  # Mistake: logging the secret.

    client = anthropic.Anthropic(api_key=api_key)
    return client


# TODO: List every mistake you found in bad_get_client() above (aim for at
# least 3 — there are more than 3 called out in the comments already; try to
# name them in your own words as if explaining to a teammate in code review):
#
# 1. The key is a literal string baked into source code. If this file is ever
#    committed, the key is permanently recoverable from git history even
#    after a later commit "removes" it -- deleting the line doesn't delete
#    the history, and automated scanners actively hunt public repos for
#    exactly this pattern.
# 2. The same literal key would be used identically across dev/staging/prod
#    if this code shipped as-is -- no per-environment scoping at all. A leak
#    or compromise in one environment compromises all of them simultaneously,
#    and there's no way to revoke/rotate access to just one environment
#    without breaking the others.
# 3. The full key is printed to stdout in `print(f"...{api_key}")`. That
#    lands in terminal scrollback, CI logs, and any log aggregation system
#    this process's output flows through -- a realistic leak path with no
#    "hacking" required, just someone reading logs they're already allowed
#    to read.
# 4. There's no explicit check for whether the key is even present/valid
#    before constructing the client -- a missing key would only surface
#    later as a less-specific SDK-level authentication error at request
#    time, instead of a clear, actionable message at the point of failure.


# ---------------------------------------------------------------------------
# TODO: Implement good_get_client().
#
# Requirements:
#   - Load ANTHROPIC_API_KEY from the environment (os.environ), not a
#     literal. If python-dotenv is installed and a local .env file exists,
#     load it first (mirror the pattern in 00-setup/verify_setup.py's
#     load_env_file(), but you may inline the logic here instead of
#     importing that module).
#   - If the key is missing, raise a clear RuntimeError explaining how to
#     fix it (export the var, or copy .env.example to .env and fill it in)
#     — do NOT let the SDK's own less-specific error be the only signal.
#   - Never print or log the key value anywhere, under any circumstances —
#     not even partially (e.g. no "here are the first 4 characters" debug
#     print). If you want to confirm a key is present without leaking it,
#     it's fine to print e.g. "ANTHROPIC_API_KEY is set (44 chars)" — length
#     only, never any substring of the actual value.
#   - Return an `anthropic.Anthropic` client constructed from that key.
# ---------------------------------------------------------------------------

def good_get_client():
    """TODO: implement per the requirements above."""
    try:
        from dotenv import load_dotenv

        if os.path.exists(".env"):
            load_dotenv(".env")
    except ImportError:
        # python-dotenv isn't installed -- fine as long as the key is
        # already in the environment some other way (e.g. `export ...`).
        pass

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Either `export ANTHROPIC_API_KEY=...` "
            "in your shell, or copy .env.example to .env and fill in a real key "
            "-- see 00-setup/README.md."
        )

    # Confirm presence without leaking the value: length only, never any
    # substring of the actual key.
    print(f"ANTHROPIC_API_KEY is set ({len(api_key)} chars)")

    import anthropic

    return anthropic.Anthropic(api_key=api_key)


# ---------------------------------------------------------------------------
# TODO: Key management checklist.
#
# Fill in this comment block with the key-management best practices from
# the README (section 4.1). Write it as if it were a checklist a teammate
# could run through before shipping a feature that uses an API key. Cover
# at minimum: rotation, least privilege / scoped keys per environment, never
# logging secrets, never hardcoding, and where keys should be stored
# (env vars / secret manager) in dev vs. production.
#
# KEY MANAGEMENT CHECKLIST
# -------------------------
# [ ] Never hardcode a key as a literal in source code -- a key committed to
#     version control is permanently recoverable from history even after a
#     later commit removes it, and public-repo scanners actively hunt for
#     exactly this pattern.
# [ ] Load keys from environment variables (an untracked .env file locally,
#     kept out of version control via .gitignore) or a dedicated secret
#     manager -- never from a literal in code. In production, prefer a
#     secret manager/vault over a bare env var baked into deploy config,
#     since it adds audit logging and rotation support env vars alone don't.
# [ ] Scope keys per environment and per least-privilege need -- separate
#     keys for dev/staging/production so a leak in one doesn't compromise
#     the others, and so any one of them can be revoked/rotated without
#     affecting the rest. Prefer a narrowly-scoped key over a broad one
#     wherever the platform supports it, even if it's more setup work.
# [ ] Rotate keys periodically, and immediately after any suspected
#     exposure -- treat rotation as a routine operational practice you've
#     actually exercised, not a break-glass procedure improvised under
#     pressure the first time it's actually needed.
# [ ] Never log secrets -- request/response logging, error messages, and
#     stack traces are common accidental leak paths; a key embedded in a
#     header dump or an exception message can land in a log aggregator far
#     more people can read than were ever meant to see the key itself.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Smoke test — optional, needs a real ANTHROPIC_API_KEY.
# ---------------------------------------------------------------------------

def run_smoke_test():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("SKIPPED: run_smoke_test (no ANTHROPIC_API_KEY set). "
              "Review good_get_client()'s logic by reading it instead.")
        return

    client = good_get_client()
    response = client.messages.create(
        model="claude-haiku-4-5",  # confirmed working; a smoke test doesn't need Sonnet/Opus
        max_tokens=20,
        messages=[{"role": "user", "content": "Reply with exactly: hygiene check ok"}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    print(f"PASS: client authenticated successfully. Model said: {text.strip()}")


def check_no_hardcoded_key_in_good_client():
    """A lightweight static check: make sure good_get_client's source code
    contains no literal string that looks like a real Anthropic API key
    prefix, confirming you're loading it dynamically rather than hardcoding
    it (mirroring what an automated secret-scanner would flag in CI)."""
    import inspect

    source = inspect.getsource(good_get_client)
    assert "sk-ant-" not in source, (
        "good_get_client() appears to contain a hardcoded key literal — "
        "load it from the environment instead."
    )
    print("PASS: check_no_hardcoded_key_in_good_client")


if __name__ == "__main__":
    check_no_hardcoded_key_in_good_client()
    run_smoke_test()
    print("\nAll checks completed.")
