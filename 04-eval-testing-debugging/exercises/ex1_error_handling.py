"""
ex1_error_handling.py — CCDV-F course, Module 04 (Eval, Testing, and Debugging)

GOAL
----
Practice identifying different Claude API error conditions and choosing the right
recovery strategy for each — retry with backoff, fail fast, or fall back — instead of
handling every exception the same way.

You do NOT need a working ANTHROPIC_API_KEY to complete most of this exercise. Scenarios
1 and 3 below are deliberately constructed so they raise real SDK exceptions without
costing you anything (an intentionally invalid key, and a fully mocked/faked exception
object) — you can run them with any string in ANTHROPIC_API_KEY, or even none set, since
the calls are designed to fail before or without doing real work. Scenario 2 is a real
network call validated server-side, so with no valid key it will actually surface as an
AuthenticationError (same as scenario 1) rather than the BadRequestError it's meant to
demonstrate — see that scenario's docstring for why, and what to do about it either way.
If you don't want to run anything at all, you can still complete this exercise by reading
each TODO and writing out, as a comment, which exception type you'd catch and why.

ASSUMPTIONS ABOUT THE SDK (verify against docs.claude.com / your installed version)
------------------------------------------------------------------------------------
This exercise assumes the `anthropic` Python SDK exposes exception types along these
lines, all deriving from `anthropic.APIError`:

  - anthropic.APIConnectionError   -- never got a response (network/DNS/TLS failure)
  - anthropic.APITimeoutError      -- client-side timeout waiting for a response
  - anthropic.APIStatusError       -- base class for any HTTP-status-coded failure;
                                       has .status_code and .message
      - anthropic.AuthenticationError     (401)
      - anthropic.PermissionDeniedError   (403)
      - anthropic.NotFoundError           (404)
      - anthropic.ConflictError           (409)
      - anthropic.RequestTooLargeError    (413)
      - anthropic.RateLimitError          (429)
      - anthropic.InternalServerError     (500)
      - anthropic.BadRequestError         (400 -- covers both malformed requests AND
                                            context-length-exceeded; check the message
                                            text to tell them apart, see Scenario 2)
      - anthropic.OverloadedError         (529)

(Confirmed against `anthropic` package version 1.0.0 at the time this module was
written -- run `python -c "import anthropic; print(sorted(n for n in dir(anthropic) if
n.endswith('Error')))"` yourself to see exactly what your installed version exports,
since names and hierarchy do shift between SDK versions.)

pip install anthropic   (see ../../00-setup for full environment setup)
"""

import os
import random
import time

import anthropic

# NOTE: the docstring above assumes the SDK's HTTP dependency is `httpx`, which is the
# normal case -- but the `anthropic` version actually installed here (1.1.0) depends on
# a package called `httpx2` instead, and anthropic.RateLimitError's constructor expects
# an httpx2.Response, not an httpx.Response. Plain `httpx` isn't even installed in this
# environment. This is exactly the "verify against your installed version" warning
# above, discovered by actually trying to run this -- check
# `pip show anthropic` / your installed SDK's actual dependency before assuming `httpx`
# is right for you.
import httpx2 as httpx

MODEL = "claude-haiku-4-5"


# ---------------------------------------------------------------------------
# Scenario 1: Authentication error (real API call, real exception, no cost)
# ---------------------------------------------------------------------------
def scenario_1_invalid_api_key() -> None:
    """
    An obviously-invalid API key is used to make a real call. The API will reject it
    with a 401 before doing any model work, so this costs nothing even with billing
    enabled on a real account.

    TODO:
      1. Construct an `anthropic.Anthropic` client with api_key="sk-ant-invalid-key-demo"
         (deliberately wrong -- do NOT use your real key here).
      2. Call client.messages.create(...) with any minimal valid request (model=MODEL,
         max_tokens=10, a one-line user message).
      3. Catch the specific exception type this should raise. This is NOT a transient
         error -- decide and comment on the right recovery strategy: retry, fail fast,
         or fallback? Print a message showing you made that decision, don't just print
         the raw exception.
    """
    print("\n--- Scenario 1: invalid API key ---")
    client = anthropic.Anthropic(api_key="sk-ant-invalid-key-demo")
    try:
        client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}],
        )
    except anthropic.AuthenticationError as e:
        # Not transient: the credential itself is wrong, and retrying with the same
        # key will fail identically every time. Recovery strategy: FAIL FAST -- log
        # clearly and stop, so a human fixes the key/config. Retrying would just burn
        # time and (on a real account) still never succeed.
        print(f"Fail fast (auth error, needs a config fix, not a retry): {e}")


# ---------------------------------------------------------------------------
# Scenario 2: Malformed / invalid request (real call, no cost -- rejected before
# any model work happens)
# ---------------------------------------------------------------------------
def scenario_2_invalid_request() -> None:
    """
    Send a request that the API will reject as structurally invalid: max_tokens=0
    is out of the allowed range for the Messages API.

    (We use an out-of-range parameter rather than an oversized context window here,
    because deliberately building a prompt that exceeds a model's context window would
    mean sending -- and paying to process -- an enormous request. A parameter
    validation error exercises the same "invalid_request_error / 400, don't retry"
    code path far more cheaply. See the docstring notes below for how a real
    context-length-exceeded error would look instead.)

    IMPORTANT: the API checks authentication BEFORE it validates the request body. If
    ANTHROPIC_API_KEY isn't set to a real, valid key, this call will raise
    AuthenticationError (same as scenario 1) instead of the BadRequestError we're trying
    to demonstrate here -- you'll never even reach request validation. That ordering is
    itself worth internalizing: you cannot assume "I got error type X" means "the thing
    I was testing for is what triggered it" without checking what came earlier in the
    pipeline. If you have a real key, run this for real. If you don't, read through the
    TODO and write your catch/recovery logic anyway -- then, as a comment, note which
    exception you'd actually see with no valid key (AuthenticationError) versus what a
    real key would produce here (BadRequestError, 400).

    TODO:
      1. Build a client, passing api_key=os.environ.get("ANTHROPIC_API_KEY",
         "sk-ant-invalid-key-demo") explicitly -- this guarantees a real network call
         even with no key set at all. (anthropic.Anthropic() with truly no key
         anywhere raises a local TypeError instead, which would skip the network
         round-trip this scenario is about.)
      2. Call client.messages.create(model=MODEL, max_tokens=0, messages=[...]).
      3. Catch BOTH anthropic.BadRequestError and anthropic.AuthenticationError in
         separate except clauses, and print which one actually fired, with a one-line
         explanation of why (see the note above).
      4. For the BadRequestError branch specifically: decide and print the recovery
         strategy. (Hint: retrying the identical request will fail identically every
         time -- what should happen instead?)

    NOTE for your own understanding (no code needed): a genuine context-length-exceeded
    failure would raise the *same* exception class as this scenario (both are
    `invalid_request_error`, HTTP 400) but the *message text* would talk about token
    counts / context window instead of an out-of-range parameter. Programmatically
    distinguishing "bad parameter" from "context too long" means inspecting
    `str(exception)` or `exception.message`, not just the exception type or status code.
    """
    print("\n--- Scenario 2: invalid request (max_tokens=0) ---")
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", "sk-ant-invalid-key-demo")
    )
    try:
        client.messages.create(
            model=MODEL,
            max_tokens=0,
            messages=[{"role": "user", "content": "Hello"}],
        )
    except anthropic.AuthenticationError as e:
        # With no valid key set, auth is checked BEFORE the request body is validated,
        # so this fires instead of BadRequestError -- it does NOT mean max_tokens=0
        # was actually fine. With a real key, the same call would raise
        # BadRequestError (400, invalid_request_error) instead.
        print(f"AuthenticationError fired first (no valid key set), not BadRequestError: {e}")
    except anthropic.BadRequestError as e:
        # Recovery strategy: FAIL FAST. Retrying the identical malformed request
        # (max_tokens=0) will fail identically every time -- the fix is to correct
        # the request in code, not to retry it.
        print(f"Fail fast (bad request, needs a code fix, not a retry): {e}")


# ---------------------------------------------------------------------------
# Scenario 3: Rate limit -- simulated, no real quota burned
# ---------------------------------------------------------------------------
class FlakyRateLimitedClient:
    """
    A tiny fake stand-in for anthropic.Anthropic that raises a real
    anthropic.RateLimitError on its first two calls, then succeeds, so you can
    practice a retry-with-backoff loop without ever touching a real account's
    rate limit.

    Do not try to actually exhaust a real rate limit to practice this -- it's slow,
    costs money, and is unnecessary when the exception type is what you're practicing
    against.
    """

    def __init__(self, fail_times: int = 2):
        self._fail_times = fail_times
        self._calls = 0

    def create_message(self):
        self._calls += 1
        if self._calls <= self._fail_times:
            # Construct a real RateLimitError the same way the SDK would receive one:
            # APIStatusError subclasses require an httpx.Response (and a body) in real
            # usage, so we build the minimal httpx objects the exception needs. httpx
            # is a real dependency of the anthropic package, so this import is safe.
            request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            response = httpx.Response(status_code=429, request=request)
            raise anthropic.RateLimitError(
                message="rate_limit_error: simulated for practice",
                response=response,
                body={"type": "error", "error": {"type": "rate_limit_error"}},
            )
        return {"content": [{"text": "ok, this is the fake successful response"}]}


def scenario_3_rate_limit_with_backoff() -> None:
    """
    Use FlakyRateLimitedClient above to practice a bounded exponential-backoff-with-
    jitter retry loop against a *real* anthropic.RateLimitError -- just one that's
    simulated locally instead of triggered against the real API.

    TODO:
      1. Instantiate FlakyRateLimitedClient().
      2. Write a loop that calls .create_message(), catches anthropic.RateLimitError,
         and retries with exponential backoff + jitter, up to a max of (say) 5 attempts.
         - Compute delay as something like: base_delay * (2 ** attempt_number)
         - Add jitter: a small random amount added to or multiplying that delay, so
           repeated runs don't produce identical timing.
         - For this exercise, print the computed delay instead of actually sleeping
           the full amount (or sleep a tiny fraction of it) so the script runs fast --
           note in a comment where a real `time.sleep(delay)` would go.
      3. On success, print the response. If you exhaust all attempts without success,
         print a clear failure message instead of raising an unhandled exception.
      4. Comment: why is retrying the right strategy here, in contrast to scenarios 1
         and 2?
    """
    print("\n--- Scenario 3: simulated rate limit with backoff ---")
    client = FlakyRateLimitedClient()

    max_attempts = 5
    base_delay = 0.5  # seconds
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.create_message()
            print(f"Success on attempt {attempt}: {response}")
            break
        except anthropic.RateLimitError as e:
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            print(f"Attempt {attempt}/{max_attempts} rate-limited ({e}); "
                  f"backing off {delay:.2f}s")
            # Real code would do: time.sleep(delay)
            time.sleep(delay / 100)  # sleep a tiny fraction so this exercise runs fast
    else:
        print(f"Exhausted all {max_attempts} attempts without success.")

    # Why retry here but not in scenarios 1/2: a RateLimitError is transient and
    # self-correcting -- the server is asking the caller to slow down, not telling it
    # the credentials or the request itself are wrong. The identical request will very
    # likely succeed later once the rate limit window passes, which is exactly what
    # retry-with-backoff is for. Scenarios 1 and 2 are structural problems (bad key,
    # bad request) that retrying the same call can never fix on its own.


# ---------------------------------------------------------------------------
# Scenario 4: put it together -- one dispatcher with per-exception-type strategy
# ---------------------------------------------------------------------------
def call_with_recovery_strategy(client: anthropic.Anthropic, **create_kwargs):
    """
    TODO: write a single reusable function that wraps client.messages.create(**create_kwargs)
    and applies DIFFERENT recovery logic depending on exception type:

      - anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError,
        or an anthropic.APIStatusError with status_code in {500, 529}:
            retry with exponential backoff + jitter, bounded attempts, then re-raise if
            still failing.
      - anthropic.AuthenticationError, anthropic.PermissionDeniedError, or an
        anthropic.APIStatusError with status_code in {400, 404}:
            fail fast -- do not retry, raise/log immediately with a clear message
            explaining this needs a code/config fix, not a retry.
      - anything else unexpected:
            log it clearly and re-raise -- don't swallow unknown failures silently.

    This is the shape a real application's API-calling layer should have: ONE place
    that knows how to route each failure type to the right strategy, rather than
    scattering ad-hoc try/except blocks through the codebase.
    """
    max_attempts = 5
    base_delay = 0.5
    RETRY_STATUS = {429, 500, 529}  # RateLimitError, InternalServerError, OverloadedError
    FAIL_FAST_STATUS = {400, 404}  # AuthenticationError(401)/PermissionDeniedError(403)
    # are handled by isinstance below rather than by status code, since they need their
    # own clear message, but they fail fast the same way.

    def _retry_or_raise(exc, attempt, reason):
        # NOTE: this is a nested helper (not inline code after the except blocks)
        # specifically to avoid a Python gotcha: the name bound by `except E as e`
        # is automatically deleted once that except block exits, so `raise e` after
        # falling out of the except clause would fail with "e is not defined" (or
        # worse, a bare `raise` outside an except block raises RuntimeError, since
        # there's no "currently handled exception" once you've left the block).
        # Calling this helper *from inside* the except block, passing `exc` as an
        # ordinary argument, sidesteps that entirely.
        if attempt >= max_attempts:
            print(f"Giving up after {attempt} attempts ({reason}).")
            raise exc
        delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
        print(f"{reason}, attempt {attempt}/{max_attempts}, backing off {delay:.2f}s")
        # Real code would do: time.sleep(delay)
        time.sleep(delay / 100)

    attempt = 0
    while True:
        attempt += 1
        try:
            return client.messages.create(**create_kwargs)
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
            # Never got a usable response at all -- transient network/DNS/TLS issue,
            # or a client-side timeout. Worth retrying.
            _retry_or_raise(e, attempt, type(e).__name__)
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            # Credential/permission problem -- retrying the same call can never fix
            # this. Needs a human to fix the key/config.
            print(f"Fail fast: {type(e).__name__} needs a code/config fix, not a retry. {e}")
            raise
        except anthropic.APIStatusError as e:
            status = e.status_code
            if status in RETRY_STATUS:
                _retry_or_raise(e, attempt, f"{type(e).__name__} (status {status})")
            elif status in FAIL_FAST_STATUS:
                print(
                    f"Fail fast: {type(e).__name__} (status {status}) needs a "
                    f"code/config fix, not a retry. {e}"
                )
                raise
            else:
                # Something with an HTTP status we didn't specifically plan for
                # (e.g. 409 Conflict, 413 RequestTooLarge) -- don't guess at a
                # strategy for it silently, surface it clearly instead.
                print(f"Unhandled status {status} ({type(e).__name__}): {e} -- re-raising")
                raise
        except Exception as e:
            # Anything not an anthropic API error at all -- never swallow silently.
            print(f"Unexpected error type {type(e).__name__}: {e} -- re-raising")
            raise


if __name__ == "__main__":
    print("Module 04 / Exercise 1: Error Handling")
    print("=" * 60)
    scenario_1_invalid_api_key()
    scenario_2_invalid_request()
    scenario_3_rate_limit_with_backoff()
    print("\nAll scenarios complete. See solutions/ex1_error_handling.py to check your work.")
