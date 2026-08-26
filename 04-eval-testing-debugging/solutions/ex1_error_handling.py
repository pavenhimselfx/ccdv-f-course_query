"""
solutions/ex1_error_handling.py — CCDV-F course, Module 04 (Eval, Testing, and Debugging)

Reference solution for exercises/ex1_error_handling.py. Read the exercise file's
docstrings first and try it yourself before reading this.

This solution was run against `anthropic` SDK version 1.0.0. If your installed version
differs, exception names/behavior may differ slightly -- check docs.claude.com.
"""

import os
import random
import time

import anthropic
import httpx

MODEL = "claude-haiku-4-5"


# ---------------------------------------------------------------------------
# Scenario 1: Authentication error
# ---------------------------------------------------------------------------
def scenario_1_invalid_api_key() -> None:
    print("\n--- Scenario 1: invalid API key ---")
    client = anthropic.Anthropic(api_key="sk-ant-invalid-key-demo")

    try:
        client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "hello"}],
        )
    except anthropic.AuthenticationError as e:
        # Recovery strategy: FAIL FAST. This is not a transient condition -- the key
        # is wrong, and no amount of retrying with the same key will ever succeed.
        # Retrying here would just burn latency and (if this were a real endpoint under
        # load) add needless traffic. The right move is to surface a clear, actionable
        # error immediately: check credentials/config, don't loop.
        print(f"  Caught AuthenticationError (status {e.status_code}): {e.message}")
        print("  Recovery strategy: FAIL FAST -- bad credentials need a config fix,")
        print("  not a retry. Surfacing this to the caller/operator immediately.")


# ---------------------------------------------------------------------------
# Scenario 2: Malformed / invalid request
# ---------------------------------------------------------------------------
def scenario_2_invalid_request() -> None:
    print("\n--- Scenario 2: invalid request (max_tokens=0) ---")
    # Pass the key explicitly (falling back to an obviously-fake placeholder) so this
    # always makes a real network call, even when ANTHROPIC_API_KEY isn't set --
    # anthropic.Anthropic() with NO key at all raises a local TypeError instead of an
    # API exception, which would skip the network round-trip this scenario is about.
    api_key = os.environ.get("ANTHROPIC_API_KEY", "sk-ant-invalid-key-demo")
    client = anthropic.Anthropic(api_key=api_key)

    try:
        client.messages.create(
            model=MODEL,
            max_tokens=0,
            messages=[{"role": "user", "content": "hello"}],
        )
        print("  No exception raised -- is max_tokens=0 actually rejected by your")
        print("  installed SDK/API version? Check docs.claude.com for current limits.")
    except anthropic.BadRequestError as e:
        # This is what we're aiming to demonstrate: a genuine 400 invalid_request_error
        # because the request itself is structurally wrong (max_tokens out of range).
        print(f"  Caught BadRequestError (status {e.status_code}): {e.message}")
        print("  Recovery strategy: FAIL FAST -- this is the SAME category as scenario 1")
        print("  (a 4xx caused by something wrong in what WE sent). Retrying an identical")
        print("  malformed request produces an identical failure every time. Fix the")
        print("  request (here: a valid max_tokens value) before calling again.")
        print("  Note: this is the same exception class a context-length-exceeded error")
        print("  would raise (both are 400 invalid_request_error) -- telling them apart")
        print("  requires reading e.message, not just catching BadRequestError.")
    except anthropic.AuthenticationError as e:
        # This branch fires if ANTHROPIC_API_KEY isn't set to a real, valid key --
        # the API validates auth BEFORE it validates the request body, so an invalid
        # key masks the BadRequestError we were trying to trigger.
        print(f"  Caught AuthenticationError (status {e.status_code}) instead.")
        print("  This means ANTHROPIC_API_KEY isn't a valid real key in this environment,")
        print("  so the request never reached body validation. Set a real key and re-run")
        print("  to see the BadRequestError this scenario is actually meant to show.")


# ---------------------------------------------------------------------------
# Scenario 3: Simulated rate limit with backoff
# ---------------------------------------------------------------------------
class FlakyRateLimitedClient:
    def __init__(self, fail_times: int = 2):
        self._fail_times = fail_times
        self._calls = 0

    def create_message(self):
        self._calls += 1
        if self._calls <= self._fail_times:
            request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            response = httpx.Response(status_code=429, request=request)
            raise anthropic.RateLimitError(
                message="rate_limit_error: simulated for practice",
                response=response,
                body={"type": "error", "error": {"type": "rate_limit_error"}},
            )
        return {"content": [{"text": "ok, this is the fake successful response"}]}


def scenario_3_rate_limit_with_backoff() -> None:
    print("\n--- Scenario 3: simulated rate limit with backoff ---")
    client = FlakyRateLimitedClient()

    max_attempts = 5
    base_delay = 0.5  # seconds -- real base delays are often 0.5-2s

    for attempt in range(max_attempts):
        try:
            result = client.create_message()
            print(f"  Success on attempt {attempt + 1}: {result['content'][0]['text']}")
            break
        except anthropic.RateLimitError as e:
            if attempt == max_attempts - 1:
                # Recovery strategy note: we've exhausted our retry budget. At this
                # point a real application should either surface a clear failure to
                # the caller, or -- if configured -- fall back to a smaller/different
                # model or reduced scope rather than looping forever.
                print(f"  Exhausted {max_attempts} attempts, giving up. Last error: {e}")
                break

            # Exponential backoff: delay doubles each attempt.
            exp_delay = base_delay * (2 ** attempt)
            # Jitter: add a random amount (here, up to 50% of the computed delay) so
            # that if many callers are retrying at once, they don't all retry in
            # lockstep and re-create the exact spike that caused the 429s.
            jitter = random.uniform(0, exp_delay * 0.5)
            delay = exp_delay + jitter

            print(
                f"  Attempt {attempt + 1} rate-limited (429). "
                f"Backing off ~{delay:.2f}s before retrying..."
            )
            # In production: time.sleep(delay)
            # For this exercise we sleep a tiny fraction so the script runs fast.
            time.sleep(min(delay, 0.05))

    # Why retry here but not in scenarios 1/2? A 429 is TRANSIENT -- it reflects
    # current load/quota state, not a permanent problem with the request itself.
    # The identical request is very likely to succeed a moment later once the rate
    # window resets, which is exactly the condition backoff-with-jitter is for.
    # Contrast with scenarios 1 and 2, where the request was permanently wrong and
    # retrying would never help.


# ---------------------------------------------------------------------------
# Scenario 4: single dispatcher applying per-exception-type strategy
# ---------------------------------------------------------------------------
def call_with_recovery_strategy(client, max_attempts: int = 4, base_delay: float = 0.5, **create_kwargs):
    """
    One reusable call path that routes each exception type to the right strategy.
    Real applications should centralize this logic instead of duplicating retry loops
    (or, worse, ad-hoc inconsistent handling) at every call site.
    """
    transient_status_codes = {500, 529}
    fail_fast_status_codes = {400, 404}

    for attempt in range(max_attempts):
        try:
            return client.messages.create(**create_kwargs)

        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError):
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
            print(f"  [recovery] transient error, retrying in ~{delay:.2f}s "
                  f"(attempt {attempt + 1}/{max_attempts})")
            time.sleep(min(delay, 0.05))  # trimmed for exercise speed

        except anthropic.APIStatusError as e:
            if e.status_code in transient_status_codes:
                if attempt == max_attempts - 1:
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
                print(f"  [recovery] status {e.status_code}, retrying in ~{delay:.2f}s "
                      f"(attempt {attempt + 1}/{max_attempts})")
                time.sleep(min(delay, 0.05))
            elif e.status_code in fail_fast_status_codes or isinstance(
                e, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)
            ):
                print(f"  [recovery] status {e.status_code} needs a code/config fix, "
                      f"not a retry: {e.message}")
                raise
            else:
                # Unrecognized status code -- don't guess, log and re-raise.
                print(f"  [recovery] unhandled status {e.status_code}, re-raising: {e.message}")
                raise

        except anthropic.APIError as e:
            # Catch-all for any other SDK-level error we didn't explicitly plan for.
            # Log clearly, don't swallow it.
            print(f"  [recovery] unexpected APIError ({type(e).__name__}): {e}")
            raise


if __name__ == "__main__":
    print("Module 04 / Exercise 1: Error Handling — SOLUTION")
    print("=" * 60)
    scenario_1_invalid_api_key()
    scenario_2_invalid_request()
    scenario_3_rate_limit_with_backoff()
    print("\nDone. call_with_recovery_strategy() above shows how to combine all of this")
    print("into one reusable call path instead of scattering try/except everywhere.")
