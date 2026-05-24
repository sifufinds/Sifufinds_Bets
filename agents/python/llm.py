"""
AI wrapper — Groq primary (free, fast), Gemini fallback.

Groq free tier: 6,000 requests/day on llama-3.3-70b-versatile.
Get a free key at: https://console.groq.com → API Keys → Create

Gemini fallback: requires billing on the Google project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

_groq_key = os.getenv("GROQ_API_KEY", "")
_gemini_key = os.getenv("GEMINI_API_KEY", "")

if not _groq_key and not _gemini_key:
    raise RuntimeError("No AI key found. Set GROQ_API_KEY in agents/python/.env")

# ── Groq client (primary — free tier) ────────────────────────────────────────
_groq_client = None
if _groq_key:
    from groq import Groq
    _groq_client = Groq(api_key=_groq_key)
    _GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Gemini client (fallback) ──────────────────────────────────────────────────
_gemini_client = None
if _gemini_key:
    from google import genai
    from google.genai import types as _gtypes
    _gemini_client = genai.Client(api_key=_gemini_key)
    _GEMINI_MODEL = "gemini-1.5-flash"


def ask(system_prompt: str, user_message: str) -> str:
    return _ask_with_fallback(system_prompt, user_message, max_tokens=4096)


def ask_long(system_prompt: str, user_message: str) -> str:
    return _ask_with_fallback(system_prompt, user_message, max_tokens=8000)


def _ask_with_fallback(system_prompt: str, user_message: str, max_tokens: int) -> str:
    if _groq_client:
        try:
            return _ask_groq(system_prompt, user_message, max_tokens)
        except Exception as e:
            err = str(e).lower()
            # Fall through to Gemini on rate limit or quota errors
            if "rate_limit" in err or "429" in err or "quota" in err or "tokens" in err:
                if _gemini_client:
                    print(f"[llm] Groq rate-limited — falling back to Gemini")
                    return _ask_gemini(system_prompt, user_message, max_tokens)
            raise
    if _gemini_client:
        return _ask_gemini(system_prompt, user_message, max_tokens)
    raise RuntimeError("No AI provider available")


def _ask_groq(system_prompt: str, user_message: str, max_tokens: int) -> str:
    response = _groq_client.chat.completions.create(
        model=_GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.8,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def _ask_gemini(system_prompt: str, user_message: str, max_tokens: int) -> str:
    from google.genai import types as _gtypes
    response = _gemini_client.models.generate_content(
        model=_GEMINI_MODEL,
        contents=user_message,
        config=_gtypes.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()
