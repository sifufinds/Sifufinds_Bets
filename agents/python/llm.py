"""
AI wrapper — Groq primary (4 models, each its own free daily quota), then
two genuinely-free, open-source, no-signup, no-API-key fallbacks: g4f, then
local Ollama. Deliberately does NOT fall back to any paid or signup-gated
API (Claude, Gemini, etc.) — see the 2026-08-10 removal note below.

Fallback chain (each tier is tried before the next):
  1. Groq openai/gpt-oss-120b      — best quality, separate free TPD quota
  2. Groq qwen/qwen3.6-27b         — separate free TPD quota
  3. Groq openai/gpt-oss-20b       — faster, separate free TPD quota
  (llama-3.3-70b-versatile and llama-3.1-8b-instant, previously tiers 1-2,
  were retired by Groq — see the 2026-08-21 note below on _GROQ_MODELS)
  5. g4f (Yqcloud →                — no signup, no API key, no billing;
     CohereForAI_C4AI_Command)        hosted (seconds, not CPU-bound
                                      minutes) open-source aggregator of
                                      free reverse-engineered LLM
                                      front-ends (github.com/xtekky/gpt4free)
  6. Local Ollama (llama3.1:8b)    — no signup, no API key, no billing;
                                     open-weight model, installed + started
                                     on demand only once every tier above
                                     has failed; the only tier with zero
                                     dependency on any third-party service
                                     staying up

Groq bills tokens-per-day (TPD) per model, not per account, so a model
sitting near its cap doesn't touch the other three — that's why tiers 1-4
are all Groq: each exhausted model just falls through to the next one on
the same free key instead of jumping straight to tier 5.

Per-minute rate limits (RPM) are retried once after the suggested delay.
Daily token limits (TPD) are NOT retried inline — Groq's real TPD reset is a
rolling window (minutes to hours since that model's quota was last consumed,
not a fixed midnight-UTC cliff), so waiting the RPM-sized cap before retrying
just wastes job time. They fall through to the next tier immediately instead.

Tiers 5-6 exist because this repo runs ~10 different scheduled agents off
one shared free Groq key (see AGENT-KNOWLEDGE.md 2026-08-01) — cumulative
usage across all of them can exhaust every Groq model's daily quota on a
busy day.

g4f (tier 5, added 2026-08-08) is tried before Ollama because it is hosted
(a real GPT-4o-mini/GPT-4-class response in 1-9s in testing, vs. Ollama's
multi-minute CPU-only inference) — but it works by proxying free public
chat front-ends, not a stable documented API, so individual g4f
providers/models can and do break without notice. Every call is wrapped in
a hard wall-clock timeout and any failure (exception, timeout, or empty
response) falls straight through to the next model in _G4F_PROVIDERS, then
to Ollama — this tier is a pure bonus, never a dependency the rest of the
pipeline assumes is up.

Local Ollama (tier 6) is deliberately only installed/started lazily inside
_ensure_ollama() the first time it's actually needed in a given process —
never as a workflow-level setup step — so the common case (a Groq or g4f
model succeeds) pays zero extra latency or CI minutes. Quality is well
below the 70B-class Groq models; this is a last resort, not a replacement.

Upgraded from llama3.2:3b to llama3.1:8b on 2026-08-08 (see
AGENT-KNOWLEDGE.md): with Groq TPD saturated most of the day across the
growing agent fleet, Ollama had become the *de facto primary* writer for
transfers content, not an occasional fallback — and 3b was hallucinating
specific transfer fees/quotes not in the source snippets often enough that
agent_fact_checker.py was correctly blocking essentially 100% of drafts
for a 12+ hour stretch. 8b is still a genuinely free/local/no-signup model
(same zero-cost property that made 3b the chosen tier) but follows the
"never invent a fee/quote" instruction meaningfully more reliably. g4f
(added the same day) further reduces how often Ollama is even reached.

ask()/ask_long() accept prefer_accuracy=True to swap tiers 5-6 to
Ollama-then-g4f instead of the default g4f-then-Ollama. Added 2026-08-10
after a live 3-day content blackout (2026-08-07 to 2026-08-10, see
AGENT-KNOWLEDGE.md) in which g4f kept returning non-empty drafts for
transfer_news.yml that agent_fact_checker.py correctly rejected for
inventing specific transfer fees — g4f "succeeding" isn't the same as g4f
being accurate. Use this for any caller whose output is fact-sensitive
(specific figures/dates/quotes that are cheap for a weak free model to
invent and expensive to get wrong on a betting site); leave it off for
everything else so the common case keeps g4f's latency advantage.

Claude and Gemini tiers were removed entirely on 2026-08-10 at the user's
explicit direction: no paid, billing-gated, or signup/API-key-requiring
fallback of any kind, full stop — free, open-source, no-signup tools only.
Groq itself still needs a (free) API key, but it was already the
established primary before this policy and isn't a new dependency; g4f and
Ollama need no key or signup at all. If Groq + g4f + Ollama are all
unavailable, generation fails loudly (AIProvidersExhausted) rather than
reaching for a paid tier.

Get a free Groq key at: https://console.groq.com → API Keys → Create
g4f and Ollama need no key or signup at all — see tiers 5-6 above.
"""
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


class AIProvidersExhausted(RuntimeError):
    """Every configured LLM provider is rate-limited or over its daily quota.

    Distinct from a bare RuntimeError so callers can tell "the AI backend is
    down" (an infra failure worth retrying/alerting on) apart from ordinary
    content-generation problems (bad JSON, no fresh news) that are fine to
    skip silently. See agent_sports_blog.generate_post for the split.
    """


_groq_key = os.getenv("GROQ_API_KEY", "")

# ── Groq client (tiers 1-4 — all free, separate quota per model) ────────────
_groq_client = None
if _groq_key:
    from groq import Groq
    _groq_client = Groq(api_key=_groq_key)
else:
    print("[llm] ⚠ GROQ_API_KEY not set — relying entirely on the free "
          "no-signup g4f + Ollama tiers.")

# llama-3.3-70b-versatile and llama-3.1-8b-instant were retired by Groq —
# confirmed 2026-08-21 via GET https://api.groq.com/openai/v1/models with
# the live production key: neither appears in the current model list at
# all. This was a total, silent content blackout (not just these two models
# degraded): every single call hit llama-3.3-70b-versatile first, got a 404
# invalid_request_error/model_not_found (not rate-limit shaped), and the
# per-model exception handler in _ask_with_fallback() used to `raise` on
# any non-rate-limit error — killing the whole function before it ever
# reached the other 3 models, g4f, or Ollama. That handler is fixed now
# (falls through instead of raising), but a dead model still wastes a
# guaranteed-failed call every single time, so it's removed here too.
# Replaced with qwen/qwen3.6-27b, confirmed present in that same live model
# list, for a 3rd genuinely-distinct quota bucket alongside the two
# gpt-oss sizes. Re-verify with the same GET request if content generation
# ever silently stops again — Groq can retire/rename models without notice.
_GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-20b",
]

# ── g4f client (tier 5 — free, no signup, no API key, no billing) ───────────
# github.com/xtekky/gpt4free — aggregates many free reverse-engineered LLM
# front-ends behind one OpenAI-style interface. Genuinely optional: if the
# package isn't installed (e.g. a local dev env that skipped it), this tier
# is just absent from the chain rather than raising.
_g4f_client = None
_G4F_PROVIDERS: list[tuple[object, str, str]] = []  # (provider_class, model, label)

# Deliberately PINNED to specific provider classes instead of leaving
# model="gpt-4o-mini" etc. to g4f's own auto-provider-selection. Confirmed
# live 2026-08-08: on the actual GitHub Actions runner (not just this dev
# machine), g4f's auto-selection routed straight to providers that need real
# credentials — "GithubCopilot: MissingAuthError ... run 'g4f auth
# github-copilot'" and "Nvidia: PaymentRequiredError: No cake credits" — so
# every g4f attempt failed and the tier was a total no-op in production
# despite passing every local test.
#
# REPLACED 2026-08-22: the original WeWordle/OperaAria/Cloudflare trio (all
# individually live-tested on 2026-08-08) had silently rotted to a 100%
# failure rate by this date — found while diagnosing a multi-day blog-post
# drought (posts.json had zero new entries for 2026-08-22 despite 10+
# breaking_news.yml runs). Live-tested against g4f 8.1.7 on this date:
# WeWordle no longer exists in g4f.Provider at all (AttributeError);
# OperaAria now 401s against oauth2.opera-api.com (needs auth it didn't
# before); Cloudflare fails with "Failed to start shared Chrome" (needs a
# local headless browser this environment doesn't have). With g4f
# unconditionally dead, EVERY Groq-exhausted call across every writer agent
# was falling straight through to local Ollama — which needs a fresh ~4.9GB
# model pull on every ephemeral GitHub Actions runner (no cache persists
# between jobs) plus multi-minute CPU-only inference, blowing every
# per-category timeout in practice (see breaking_news.yml's football
# category timing out at its full 600s with zero output).
#
# Replaced with two providers tested clean against both a short JSON
# fact-check prompt and a full 700+ word article-generation prompt, same
# methodology as the entry above: Yqcloud (fastest, ~3-42s, zero extra pip
# deps) first; CohereForAI_C4AI_Command (~1-25s, zero extra pip deps, best
# observed instruction-following — followed a strict "JSON only, no
# markdown fences" instruction on the first attempt) second. Both confirmed
# with zero additional packages beyond what requirements.txt already
# installs — no browser, no HAR file, no API key. Re-verify this list with
# the test snippet in AGENT-KNOWLEDGE.md's 2026-08-22 entry if g4f is ever
# touched again — individual providers break/get patched without notice,
# exactly as happened here.
#
# Each provider is imported independently (fixed 2026-08-08): the original
# code imported all three under one try/except ImportError, so when g4f
# shipped a version where WeWordle alone had been renamed/removed (confirmed
# live: "cannot import name 'WeWordle' from 'g4f.Provider'" on a normal
# scheduled run), the ImportError killed OperaAria and Cloudflare too even
# though neither one was actually broken — the whole tier silently went from
# 3 working providers to 0 because of one. requirements.txt only pins
# g4f>=7.9.0 (no upper bound), so this kind of drift between what was tested
# and what actually installs on a fresh ephemeral runner is expected to
# recur; degrading per-provider instead of all-or-nothing is what actually
# fixes it, not chasing an exact version pin.
try:
    from g4f.client import Client as _G4FClient
    _g4f_client = _G4FClient()
except ImportError as e:
    print(f"[llm] g4f package not installed ({e}) — skipping the free "
          "no-signup g4f fallback tier entirely (falls through to "
          "Ollama instead). Add 'g4f' to requirements.txt.")

if _g4f_client is not None:
    for _provider_name, _model, _label in (
        ("Yqcloud", "gpt-4", "Yqcloud"),
        ("CohereForAI_C4AI_Command", "command-a", "CohereForAI_C4AI_Command"),
    ):
        try:
            import g4f.Provider as _g4f_provider_module
            _provider_cls = getattr(_g4f_provider_module, _provider_name)
            _G4F_PROVIDERS.append((_provider_cls, _model, _label))
        except AttributeError as e:
            print(f"[llm] g4f provider '{_label}' unavailable in this g4f version ({e}) — "
                  f"skipping just this provider, trying the rest of the g4f tier.")
    if not _G4F_PROVIDERS:
        print("[llm] All pinned g4f providers are unavailable in this g4f version — "
              "the g4f tier has nothing to try this run (falls through to Ollama).")

_G4F_TIMEOUT = 60  # hard wall-clock cap per provider attempt, in seconds


def _ask_g4f(system_prompt: str, user_message: str, max_tokens: int, provider, model: str) -> str:
    """g4f's client has no reliable built-in timeout (some of its providers
    can hang indefinitely on a dead upstream), so this enforces one from the
    outside via a throwaway thread — the call is synchronous, there's no
    async alternative worth threading through this module for a fallback
    tier that's expected to fail sometimes."""
    from concurrent.futures import ThreadPoolExecutor
    from concurrent.futures import TimeoutError as _FutureTimeout

    def _call() -> str:
        response = _g4f_client.chat.completions.create(
            model=model,
            provider=provider,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_call)
        try:
            return future.result(timeout=_G4F_TIMEOUT)
        except _FutureTimeout:
            raise TimeoutError(f"g4f {model} did not respond within {_G4F_TIMEOUT}s")


# ── Local Ollama fallback (tier 6 — no signup, no API key, no billing) ──────
_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
_ollama_setup_attempted = False


def _ollama_reachable(timeout: float = 2.0) -> bool:
    try:
        return requests.get(f"{_OLLAMA_HOST}/api/tags", timeout=timeout).status_code == 200
    except Exception:
        return False


def _ensure_ollama() -> bool:
    """Install Ollama + pull a small open-weight model + start the server,
    entirely on demand, the first time every tier above has already failed
    in this process. Cached via _ollama_setup_attempted so a second
    AIProvidersExhausted-bound call in the same run doesn't retry an
    install/pull that already failed (e.g. no internet egress, disk full).
    Returns False fast on any environment where this can't work (a local
    dev machine without Ollama and without sudo, a sandboxed runner with no
    outbound network)."""
    global _ollama_setup_attempted
    if _ollama_reachable():
        return True
    if _ollama_setup_attempted:
        return False
    _ollama_setup_attempted = True
    try:
        if shutil.which("ollama") is None:
            print("[llm] Installing local Ollama fallback (no signup/key required)...")
            subprocess.run("curl -fsSL https://ollama.com/install.sh | sh",
                            shell=True, check=True, timeout=180,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[llm] Starting local Ollama server...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            if _ollama_reachable():
                break
            time.sleep(1)
        else:
            print("[llm] Ollama server did not come up in time — skipping local fallback")
            return False
        print(f"[llm] Pulling local fallback model {_OLLAMA_MODEL} (one-time per runner, ~4.7GB)...")
        subprocess.run(["ollama", "pull", _OLLAMA_MODEL], check=True, timeout=900)
        return True
    except Exception as e:
        print(f"[llm] Local Ollama fallback unavailable in this environment: {e}")
        return False


def _ask_ollama(system_prompt: str, user_message: str, max_tokens: int) -> str:
    resp = requests.post(
        f"{_OLLAMA_HOST}/api/chat",
        json={
            "model": _OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.8},
        },
        # CPU-only inference on a shared runner is slow — a full-length
        # article generation can genuinely take several minutes, unlike the
        # cloud tiers above. 8b needs more headroom than the 3b model this
        # was originally sized for (see 2026-08-08 model upgrade above).
        timeout=1200,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


_RPM_KEYWORDS = ("requests per minute", "per minute", "rpm", "retry_delay", "retrydelay",
                 "please retry in", "rate limit")
_TPD_KEYWORDS = ("tokens per day", "per day", "tpd", "daily", "requests per day")


def _is_rate_limit(err: str) -> bool:
    return any(k in err for k in ("rate_limit", "429", "quota", "tokens per", "requests per",
                                   "resource_exhausted", "too many requests"))


def _is_daily_limit(err: str) -> bool:
    """True when the error is a daily (TPD) cap — cannot be resolved by a short wait.

    Groq reports real TPD exhaustion as e.g. "...on tokens per day (TPD): Limit
    100000, Used 97772... Please try again in 27m44s". Matching on the TPD/day
    keywords means it falls through to the next tier immediately instead of
    waiting the RPM-sized cap below.
    """
    return any(k in err.lower() for k in _TPD_KEYWORDS)


def _parse_retry_seconds(err: str, cap: int = 60) -> int:
    """Extract retry-after seconds from error text; return 0 if not found."""
    # Groq: "Please try again in 46m26.4s"
    m = re.search(r"try again in\s+(?:(\d+)m)?(\d+(?:\.\d+)?)s", err)
    if m:
        mins = int(m.group(1) or 0)
        secs = float(m.group(2) or 0)
        return min(int(mins * 60 + secs), cap)
    return 0


def ask(system_prompt: str, user_message: str, prefer_accuracy: bool = False) -> str:
    return _ask_with_fallback(system_prompt, user_message, max_tokens=4096, prefer_accuracy=prefer_accuracy)


def ask_long(system_prompt: str, user_message: str, prefer_accuracy: bool = False) -> str:
    return _ask_with_fallback(system_prompt, user_message, max_tokens=8000, prefer_accuracy=prefer_accuracy)


# Set once all 4 Groq models are confirmed exhausted/empty in this process.
# A single generate_post() call makes TWO ask()/ask_long() calls back to back
# (the draft, then agent_fact_checker.check_post()'s independent pass) — with
# no memoization, the second call re-probes all 4 already-dead Groq models
# from scratch, roughly doubling every cycle's wall-clock time and doubling
# the failed-request load this process adds to the shared Groq key for zero
# benefit (Groq's TPD quota doesn't reset mid-process). Confirmed live
# 2026-08-02: transfer_news.yml's 5-minute loop was spending minutes per
# cycle re-exhausting Groq twice before ever reaching Ollama. Deliberately
# process-scoped, not persisted to disk — each self-perpetuating loop
# iteration is a fresh `python agent_transfer_post.py` invocation anyway, so
# this naturally re-checks Groq every ~5 minutes, roughly matching the real
# TPD rolling-window reset cadence instead of assuming exhaustion forever.
_groq_exhausted_this_process = False

# Same rationale as _groq_exhausted_this_process just above: without this, a
# single generate_post() call's second ask() (the fact-checker pass) would
# re-attempt all 3 g4f models from scratch even after they just failed for
# the draft a few seconds earlier, doubling wall-clock time for no benefit —
# a dead g4f provider is dead for the rest of this process, not likely to
# recover in the next few seconds.
_g4f_exhausted_this_process = False


def _try_g4f(system_prompt: str, user_message: str, max_tokens: int) -> str | None:
    """Tier 5 in the default order — free, no-signup, no-API-key aggregator of
    hosted free LLM front-ends. Hosted (seconds, not CPU-bound minutes), but
    proxies reverse-engineered chat front-ends with no real guarantee of
    following strict negative instructions ("never invent a fee") — see
    _try_ollama()'s docstring for why prefer_accuracy=True runs this tier
    second instead of first."""
    global _g4f_exhausted_this_process
    if not (_g4f_client and _G4F_PROVIDERS and not _g4f_exhausted_this_process):
        if _g4f_exhausted_this_process:
            print("[llm] g4f already confirmed exhausted earlier this run — skipping")
        return None
    for i, (provider, model, label) in enumerate(_G4F_PROVIDERS):
        result = None
        try:
            result = _ask_g4f(system_prompt, user_message, max_tokens, provider, model)
        except Exception as e:
            print(f"[llm] g4f/{label} failed: {e}")
        if result:
            return result
        next_step = _G4F_PROVIDERS[i + 1][2] if i + 1 < len(_G4F_PROVIDERS) else "next tier"
        print(f"[llm] g4f/{label} exhausted or empty — trying {next_step}")
    _g4f_exhausted_this_process = True
    return None


def _try_ollama(system_prompt: str, user_message: str, max_tokens: int) -> str | None:
    """Tier 6 in the default order — local, self-hosted open-weight model.
    Slower than g4f (CPU-bound minutes, not hosted seconds) but empirically
    more likely to follow "never invent a fee/quote" (see the 2026-08-08
    3b→8b upgrade note in this module's docstring, which was driven by
    exactly this instruction-following gap).

    Confirmed live 2026-08-07 to 2026-08-10 (see AGENT-KNOWLEDGE.md): with
    Groq saturated most of the day, transfer_news.yml's g4f-first calls kept
    "succeeding" (non-empty text) while inventing specific transfer fees
    that agent_fact_checker.py correctly rejected — a 3-day content
    blackout despite the job itself reporting healthy cycles. Callers whose
    output is fact-check-sensitive (specific figures/dates that are easy to
    hallucinate and expensive to get wrong on a betting site) should pass
    prefer_accuracy=True to try this tier before g4f instead of after it."""
    if _ensure_ollama():
        try:
            return _ask_ollama(system_prompt, user_message, max_tokens)
        except Exception as e:
            print(f"[llm] Local Ollama fallback failed: {e}")
    return None


def _ask_with_fallback(system_prompt: str, user_message: str, max_tokens: int,
                        prefer_accuracy: bool = False) -> str:
    global _groq_exhausted_this_process, _g4f_exhausted_this_process
    if _groq_client and not _groq_exhausted_this_process:
        # Tiers 1-4 — four Groq models, each with its own separate free TPD
        # quota bucket, so one model capping out doesn't block the others.
        for i, model in enumerate(_GROQ_MODELS):
            result = None
            try:
                result = _ask_groq(system_prompt, user_message, max_tokens, model)
            except Exception as e:
                err = str(e)
                if _is_rate_limit(err.lower()) and not _is_daily_limit(err):
                    wait = _parse_retry_seconds(err)
                    if wait:
                        print(f"[llm] Groq {model} RPM limit — waiting {wait}s then retrying")
                        time.sleep(wait)
                        try:
                            result = _ask_groq(system_prompt, user_message, max_tokens, model)
                        except Exception as e2:
                            print(f"[llm] Groq {model} failed after retry ({str(e2)[:150]})")
                            result = None
                else:
                    # Used to `raise` here for anything that wasn't rate-limit
                    # shaped — which killed this ENTIRE function (skipping the
                    # other 3 Groq models, g4f, and Ollama) the instant Groq
                    # deprecated/renamed a model. Confirmed live 2026-08-21:
                    # "llama-3.3-70b-versatile does not exist" is a 404
                    # invalid_request_error, not rate-limit shaped, so every
                    # single call hit this branch and `raise`d — a silent,
                    # total content blackout across every writer agent
                    # (agent_sports_blog.py, agent_transfer_post.py,
                    # agent_priority_writer.py, agent_fabricated_content_fixer.py,
                    # ...) for ~4 days, invisible because AIProvidersExhausted
                    # was never reached, so the "no paid fallback" error
                    # message never surfaced either — every caller's own
                    # try/except just logged a generic exception and moved on
                    # as if nothing was published that cycle. A per-model
                    # failure of ANY kind must fall through to the next
                    # model/tier, never abort the whole resilience chain —
                    # that's what the chain exists for.
                    print(f"[llm] Groq {model} failed ({err[:150]}) — trying next model/tier")
                    result = None
            if result:
                return result
            # reasoning models (gpt-oss) can also come back with empty content
            # when hidden reasoning tokens consume the whole max_tokens budget —
            # that's not an exception, so it needs its own empty-result check.
            next_step = _GROQ_MODELS[i + 1] if i + 1 < len(_GROQ_MODELS) else \
                ("Ollama (accuracy-preferring order)" if prefer_accuracy else "g4f")
            print(f"[llm] Groq {model} exhausted or empty — trying {next_step}")
        _groq_exhausted_this_process = True
    elif _groq_exhausted_this_process:
        next_tier = "Ollama (accuracy-preferring order)" if prefer_accuracy else "g4f"
        print(f"[llm] Groq already confirmed exhausted earlier this run — skipping straight to {next_tier}")

    # Tiers 5-6 — g4f (hosted, fast, weaker instruction-following) and local
    # Ollama (slow, CPU-bound, stronger instruction-following). Default order
    # is g4f-then-Ollama, optimising for latency on the common case. Callers
    # generating fact-sensitive content (specific fees/dates/stats that are
    # cheap for a weak free model to invent and expensive to get wrong) pass
    # prefer_accuracy=True to flip the order — see _try_ollama()'s docstring
    # for the live incident that motivated this.
    if prefer_accuracy:
        result = _try_ollama(system_prompt, user_message, max_tokens) \
            or _try_g4f(system_prompt, user_message, max_tokens)
    else:
        result = _try_g4f(system_prompt, user_message, max_tokens) \
            or _try_ollama(system_prompt, user_message, max_tokens)
    if result:
        return result

    raise AIProvidersExhausted(
        "All free AI providers exhausted or rate-limited: all 4 Groq models are "
        "over their daily token quota (each resets on its own rolling window, "
        "minutes to a few hours since last used, not a fixed midnight-UTC "
        "cliff), every free g4f model failed or timed out, and the local Ollama "
        "fallback failed. No paid/signup-gated tier is configured by design — "
        "see this module's docstring."
    )


def _ask_groq(system_prompt: str, user_message: str, max_tokens: int, model: str) -> str:
    response = _groq_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.8,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
