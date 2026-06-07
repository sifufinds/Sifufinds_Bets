"""
AI wrapper — Groq primary, Claude fallback, Gemini last resort.

Fallback chain (each tier is tried before the next):
  1. Groq llama-3.3-70b-versatile  — best quality, 6,000 req/day free
  2. Groq llama-3.1-8b-instant     — faster, higher RPM limit, same free tier
  3. Claude claude-haiku-4-5        — reliable paid fallback, very cheap
  4. Gemini gemini-2.0-flash-lite  — higher free-tier RPM than full flash
  5. Gemini gemini-2.0-flash       — separate daily quota fallback

Per-minute rate limits (RPM) are retried once after the suggested delay.
Daily token limits (TPD) are not retried — they reset at midnight UTC.

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

_GROQ_MODEL_PRIMARY = "llama-3.3-70b-versatile"
_GROQ_MODEL_FAST    = "llama-3.1-8b-instant"

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
    """True when the error is a daily (TPD) cap — cannot be resolved by waiting."""
    el = err.lower()
    return any(k in el for k in _TPD_KEYWORDS) and "limit: 0" in el


def _parse_retry_seconds(err: str, cap: int = 120) -> int:
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
        # Tier 1 — Groq 70B
        try:
            return _ask_groq(system_prompt, user_message, max_tokens, _GROQ_MODEL_PRIMARY)
        except Exception as e:
            err = str(e)
            if _is_rate_limit(err.lower()):
                wait = _parse_retry_seconds(err)
                if wait and not _is_daily_limit(err):
                    print(f"[llm] Groq 70B RPM limit — waiting {wait}s then retrying")
                    time.sleep(wait)
                    try:
                        return _ask_groq(system_prompt, user_message, max_tokens, _GROQ_MODEL_PRIMARY)
                    except Exception:
                        pass
                print(f"[llm] Groq 70B rate-limited — trying Groq 8B instant")
            else:
                raise

        # Tier 2 — Groq 8B instant
        try:
            return _ask_groq(system_prompt, user_message, max_tokens, _GROQ_MODEL_FAST)
        except Exception as e:
            err = str(e)
            if _is_rate_limit(err.lower()):
                wait = _parse_retry_seconds(err)
                if wait and not _is_daily_limit(err):
                    print(f"[llm] Groq 8B RPM limit — waiting {wait}s then retrying")
                    time.sleep(wait)
                    try:
                        return _ask_groq(system_prompt, user_message, max_tokens, _GROQ_MODEL_FAST)
                    except Exception:
                        pass
                print(f"[llm] Groq 8B rate-limited — trying Claude")
            else:
                raise

    # Tier 3 — Claude (reliable paid fallback, fast)
    if _anthropic_client:
        try:
            return _ask_claude(system_prompt, user_message, max_tokens)
        except Exception as e:
            err = str(e)
            if _is_rate_limit(err.lower()):
                print(f"[llm] Claude rate-limited — falling back to Gemini")
            else:
                raise

    # Tiers 4 & 5 — Gemini models tried in order, each with its own daily quota
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
            raise RuntimeError(
                "All AI providers exhausted. Groq TPD resets at midnight UTC. "
                "Gemini free tier requires billing to be enabled on the Google Cloud project."
            )

    raise RuntimeError(
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
