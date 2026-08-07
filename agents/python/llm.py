"""
AI wrapper — Groq primary (4 models, each its own free daily quota), a
local self-hosted open-weight model as a genuinely-free last resort, then
Claude/Gemini as optional paid/billing-gated tiers if ever configured.

Fallback chain (each tier is tried before the next):
  1. Groq llama-3.3-70b-versatile  — best quality, separate free TPD quota
  2. Groq llama-3.1-8b-instant     — faster, separate free TPD quota
  3. Groq openai/gpt-oss-120b      — separate free TPD quota
  4. Groq openai/gpt-oss-20b       — separate free TPD quota
  5. Local Ollama (llama3.1:8b)    — no signup, no API key, no billing;
                                     installed + started on demand only
                                     once every tier above has failed
  6. Claude claude-haiku-4-5        — reliable paid fallback, very cheap
  7. Gemini gemini-2.0-flash-lite  — higher free-tier RPM than full flash
  8. Gemini gemini-2.0-flash       — separate daily quota fallback

Groq bills tokens-per-day (TPD) per model, not per account, so a model
sitting near its cap doesn't touch the other three — that's why tiers 1-4
are all Groq: each exhausted model just falls through to the next one on
the same free key instead of jumping straight to a paid/billing-gated tier.

Per-minute rate limits (RPM) are retried once after the suggested delay.
Daily token limits (TPD) are NOT retried inline — Groq's real TPD reset is a
rolling window (minutes to hours since that model's quota was last consumed,
not a fixed midnight-UTC cliff), so waiting the RPM-sized cap before retrying
just wastes job time. They fall through to the next tier immediately instead.

Tier 5 (Ollama) exists because this repo runs ~10 different scheduled
agents off one shared free Groq key (see AGENT-KNOWLEDGE.md 2026-08-01) —
cumulative usage across all of them can exhaust every Groq model's daily
quota on a busy day, and neither Claude nor Gemini billing is set up, which
previously meant total content silence until Groq's quota rolled over. The
local model is deliberately only installed/started lazily inside
_ensure_ollama() the first time it's actually needed in a given process —
never as a workflow-level setup step — so the common case (a Groq model
succeeds) pays zero extra latency or CI minutes. Quality is well below the
70B-class Groq models; this is a last resort, not a replacement.

Upgraded from llama3.2:3b to llama3.1:8b on 2026-08-08 (see
AGENT-KNOWLEDGE.md): with Groq TPD now saturated most of the day across the
growing agent fleet and Gemini still billing-gated, Ollama had become the
*de facto primary* writer for transfers content, not an occasional
fallback — and 3b was hallucinating specific transfer fees/quotes not in
the source snippets often enough that agent_fact_checker.py was correctly
blocking essentially 100% of drafts for a 12+ hour stretch. 8b is still a
genuinely free/local/no-signup model (same zero-cost property that made 3b
the chosen tier over a paid key or Gemini billing) but follows the
"never invent a fee/quote" instruction meaningfully more reliably. This is
a mitigation, not a fix for the underlying cause — Groq's shared quota
being oversubscribed by the number of scheduled agents on one key.

Get a free Groq key at: https://console.groq.com → API Keys → Create
Get an Anthropic key at: https://console.anthropic.com
Get a free Gemini key at: https://aistudio.google.com/app/apikey
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


_groq_key      = os.getenv("GROQ_API_KEY", "")
_gemini_key    = os.getenv("GEMINI_API_KEY", "")
_anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

if not _groq_key and not _gemini_key and not _anthropic_key:
    raise RuntimeError("No AI key found. Set GROQ_API_KEY or ANTHROPIC_API_KEY in agents/python/.env")

# ── Groq client (tiers 1-4 — all free, separate quota per model) ────────────
_groq_client = None
if _groq_key:
    from groq import Groq
    _groq_client = Groq(api_key=_groq_key)

_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

# ── Anthropic client (tier 5 — reliable paid fallback) ───────────────────────
_anthropic_client = None
if _anthropic_key:
    try:
        import anthropic as _anthropic_lib
        _anthropic_client = _anthropic_lib.Anthropic(api_key=_anthropic_key)
    except ImportError:
        # Confirmed live 2026-07-31: this silently swallowed the fact that
        # "anthropic" was missing from requirements.txt, so the "reliable
        # paid fallback" tier this module's own docstring promises had
        # never actually been installed in any CI workflow, and every
        # scheduled job silently fell straight through to Gemini/exhaustion
        # with nothing in the logs pointing at why — see AGENT-KNOWLEDGE.md.
        # A `print` here can't be missed the way a silently-empty client
        # can: it shows up in every single workflow run's log output.
        print("[llm] ⚠ ANTHROPIC_API_KEY is set but the 'anthropic' package "
              "isn't installed — Claude fallback tier is DISABLED this run. "
              "Check agents/python/requirements.txt.")
else:
    print("[llm] ⚠ ANTHROPIC_API_KEY not set — Claude fallback tier is "
          "DISABLED, relying on Groq + Gemini free tiers only.")

_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # fast + cheapest Claude

# ── Local Ollama fallback (tier 5 — no signup, no API key, no billing) ──────
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
    outbound network) so those environments fall through to Claude/Gemini
    exactly as before."""
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

# ── Gemini client (tiers 4 & 5) ───────────────────────────────────────────────
# Tried in order; each model has its own separate daily quota bucket.
_gemini_client = None
if _gemini_key:
    from google import genai
    _gemini_client = genai.Client(api_key=_gemini_key)

_GEMINI_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash"]

_RPM_KEYWORDS = ("requests per minute", "per minute", "rpm", "retry_delay", "retrydelay",
                 "please retry in", "rate limit")
_TPD_KEYWORDS = ("tokens per day", "per day", "tpd", "daily", "requests per day")


def _is_rate_limit(err: str) -> bool:
    return any(k in err for k in ("rate_limit", "429", "quota", "tokens per", "requests per",
                                   "resource_exhausted", "too many requests"))


def _is_daily_limit(err: str) -> bool:
    """True when the error is a daily (TPD) cap — cannot be resolved by a short wait.

    Groq reports real TPD exhaustion as e.g. "...on tokens per day (TPD): Limit
    100000, Used 97772... Please try again in 27m44s" — note there is no
    "limit: 0" in that message, that pattern is specific to Gemini's
    billing-not-enabled case. Matching on the TPD/day keywords alone is
    correct for both: neither can be fixed by sleeping the RPM-sized cap
    below, so both should fall through to the next tier immediately.
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
    # Gemini: retryDelay: "34s"
    m = re.search(r"retrydelay.*?['\"](\d+)s['\"]", err.lower())
    if m:
        return min(int(m.group(1)), cap)
    return 0


def ask(system_prompt: str, user_message: str) -> str:
    return _ask_with_fallback(system_prompt, user_message, max_tokens=4096)


def ask_long(system_prompt: str, user_message: str) -> str:
    return _ask_with_fallback(system_prompt, user_message, max_tokens=8000)


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


def _ask_with_fallback(system_prompt: str, user_message: str, max_tokens: int) -> str:
    global _groq_exhausted_this_process
    if _groq_client and not _groq_exhausted_this_process:
        # Tiers 1-4 — four Groq models, each with its own separate free TPD
        # quota bucket, so one model capping out doesn't block the others.
        for i, model in enumerate(_GROQ_MODELS):
            result = None
            try:
                result = _ask_groq(system_prompt, user_message, max_tokens, model)
            except Exception as e:
                err = str(e)
                if not _is_rate_limit(err.lower()):
                    raise
                if not _is_daily_limit(err):
                    wait = _parse_retry_seconds(err)
                    if wait:
                        print(f"[llm] Groq {model} RPM limit — waiting {wait}s then retrying")
                        time.sleep(wait)
                        try:
                            result = _ask_groq(system_prompt, user_message, max_tokens, model)
                        except Exception:
                            result = None
            if result:
                return result
            # reasoning models (gpt-oss) can also come back with empty content
            # when hidden reasoning tokens consume the whole max_tokens budget —
            # that's not an exception, so it needs its own empty-result check.
            next_step = _GROQ_MODELS[i + 1] if i + 1 < len(_GROQ_MODELS) else "local Ollama fallback"
            print(f"[llm] Groq {model} exhausted or empty — trying {next_step}")
        _groq_exhausted_this_process = True
    elif _groq_exhausted_this_process:
        print("[llm] Groq already confirmed exhausted earlier this run — skipping straight to local fallback")

    # Tier 5 — local, self-hosted open-weight model via Ollama. No signup,
    # no API key, no billing — installed/started on demand (see
    # _ensure_ollama()'s docstring). Tried before Claude/Gemini since those
    # are currently unconfigured/billing-gated in this repo, making Ollama
    # the only tier below that reliably works at all right now.
    if _ensure_ollama():
        try:
            return _ask_ollama(system_prompt, user_message, max_tokens)
        except Exception as e:
            print(f"[llm] Local Ollama fallback failed: {e} — trying Claude")

    # Tier 6 — Claude (reliable paid fallback, fast)
    if _anthropic_client:
        try:
            return _ask_claude(system_prompt, user_message, max_tokens)
        except Exception as e:
            err = str(e)
            if _is_rate_limit(err.lower()):
                print(f"[llm] Claude rate-limited — falling back to Gemini")
            else:
                raise

    # Tiers 7 & 8 — Gemini models tried in order, each with its own daily quota
    if _gemini_client:
        last_err: Exception | None = None
        for model in _GEMINI_MODELS:
            try:
                return _ask_gemini(system_prompt, user_message, max_tokens, model)
            except Exception as e:
                err = str(e)
                if not _is_rate_limit(err.lower()):
                    raise
                if _is_daily_limit(err):
                    # Daily limit=0 means billing not enabled for this model — skip it
                    print(f"[llm] Gemini {model} daily limit=0 (billing required) — skipping")
                    last_err = e
                    continue
                wait = _parse_retry_seconds(err)
                if wait:
                    print(f"[llm] Gemini {model} RPM limit — waiting {wait}s then retrying")
                    time.sleep(wait)
                    try:
                        return _ask_gemini(system_prompt, user_message, max_tokens, model)
                    except Exception:
                        pass
                print(f"[llm] Gemini {model} rate-limited — trying next model")
                last_err = e
        if last_err:
            raise AIProvidersExhausted(
                "All AI providers exhausted: all 4 Groq models are over their daily "
                "token quota (each resets on its own rolling window, typically "
                "minutes to a few hours after that model was last used, not a fixed "
                "midnight-UTC cliff) and Gemini's free tier requires billing to be "
                "enabled on the Google Cloud project."
            )

    raise AIProvidersExhausted(
        "All AI providers exhausted or rate-limited: all 4 Groq models are over "
        "their daily token quota. Each resets on its own rolling window "
        "(minutes to a few hours since last used), not a fixed midnight-UTC cliff."
    )


def _ask_claude(system_prompt: str, user_message: str, max_tokens: int) -> str:
    response = _anthropic_client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=min(max_tokens, 4096),
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


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


def _ask_gemini(system_prompt: str, user_message: str, max_tokens: int, model: str) -> str:
    from google.genai import types as _gtypes
    response = _gemini_client.models.generate_content(
        model=model,
        contents=user_message,
        config=_gtypes.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()
