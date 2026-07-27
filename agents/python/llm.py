"""
AI wrapper — Groq primary (4 models, each its own free daily quota), Claude
fallback, Gemini last resort.

Fallback chain (each tier is tried before the next):
  1. Groq llama-3.3-70b-versatile  — best quality, separate free TPD quota
  2. Groq llama-3.1-8b-instant     — faster, separate free TPD quota
  3. Groq openai/gpt-oss-120b      — separate free TPD quota
  4. Groq openai/gpt-oss-20b       — separate free TPD quota
  5. Claude claude-haiku-4-5        — reliable paid fallback, very cheap
  6. Gemini gemini-2.0-flash-lite  — higher free-tier RPM than full flash
  7. Gemini gemini-2.0-flash       — separate daily quota fallback

Groq bills tokens-per-day (TPD) per model, not per account, so a model
sitting near its cap doesn't touch the other three — that's why tiers 1-4
are all Groq: each exhausted model just falls through to the next one on
the same free key instead of jumping straight to a paid/billing-gated tier.

Per-minute rate limits (RPM) are retried once after the suggested delay.
Daily token limits (TPD) are NOT retried inline — Groq's real TPD reset is a
rolling window (minutes to hours since that model's quota was last consumed,
not a fixed midnight-UTC cliff), so waiting the RPM-sized cap before retrying
just wastes job time. They fall through to the next tier immediately instead.

Get a free Groq key at: https://console.groq.com → API Keys → Create
Get an Anthropic key at: https://console.anthropic.com
Get a free Gemini key at: https://aistudio.google.com/app/apikey
"""
import os
import re
import time
from pathlib import Path
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

# ── Groq client (tiers 1 & 2 — both free) ────────────────────────────────────
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

# ── Anthropic client (tier 3 — reliable paid fallback) ───────────────────────
_anthropic_client = None
if _anthropic_key:
    try:
        import anthropic as _anthropic_lib
        _anthropic_client = _anthropic_lib.Anthropic(api_key=_anthropic_key)
    except ImportError:
        pass  # anthropic package not installed — skip this tier

_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # fast + cheapest Claude

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


def _ask_with_fallback(system_prompt: str, user_message: str, max_tokens: int) -> str:
    if _groq_client:
        # Tiers 1-4 — four Groq models, each with its own separate free TPD
        # quota bucket, so one model capping out doesn't block the others.
        for i, model in enumerate(_GROQ_MODELS):
            try:
                return _ask_groq(system_prompt, user_message, max_tokens, model)
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
                            return _ask_groq(system_prompt, user_message, max_tokens, model)
                        except Exception:
                            pass
                next_step = _GROQ_MODELS[i + 1] if i + 1 < len(_GROQ_MODELS) else "Claude"
                print(f"[llm] Groq {model} exhausted — trying {next_step}")

    # Tier 5 — Claude (reliable paid fallback, fast)
    if _anthropic_client:
        try:
            return _ask_claude(system_prompt, user_message, max_tokens)
        except Exception as e:
            err = str(e)
            if _is_rate_limit(err.lower()):
                print(f"[llm] Claude rate-limited — falling back to Gemini")
            else:
                raise

    # Tiers 6 & 7 — Gemini models tried in order, each with its own daily quota
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
                "All AI providers exhausted. Groq TPD resets at midnight UTC. "
                "Gemini free tier requires billing to be enabled on the Google Cloud project."
            )

    raise AIProvidersExhausted(
        "All AI providers exhausted or rate-limited. "
        "Groq TPD resets at midnight UTC."
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
