"""
Country Localisation Agent — translates blog posts into the locales
gen_blog_post_pages.py already knows how to render (blog/{slug}-{locale}/,
with hreflang/OG-locale wiring already in place at gen_blog_post_pages.py:
1554-1601) but that have little or no actual translated content yet.

Started as a European-Portuguese-only agent, generalised to cover every
locale in LOCALES below (the `pt` -> `pt_PT` OG-locale mapping already
anticipates European Portuguese specifically, not Brazilian). fr/de already
have manually-populated blog/translations/{fr,de}.json files but — like
es/pt/sw — have NOT kept pace with new posts.json growth (168 translated
entries each vs 799 total posts at the time this agent was written), so this
agent is genuinely useful across all five locales, not just seeding the
empty ones.

Resumable batch pattern mirrors agent_content_backfill.py: a small batch per
run, tracked in translate_state.json (keyed by locale) so a large backlog
never needs to finish in one run, and a post that keeps failing translation
gets benched after MAX_ATTEMPTS rather than retried forever.

Usage:
    python agent_translate.py                  # auto-picks the locale with the biggest backlog
    python agent_translate.py --locale pt       # translate a batch into European Portuguese
    python agent_translate.py --locale fr --batch-size 8
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask_long, AIProvidersExhausted
from utils.logger import log

BASE = Path(__file__).parent.parent.parent
POSTS_JSON = BASE / "blog" / "posts.json"
TRANSLATIONS_DIR = BASE / "blog" / "translations"
STATE_PATH = Path(__file__).parent / "translate_state.json"

# Must stay in sync with LOCALES in gen_blog_post_pages.py — that's what
# actually renders blog/{slug}-{locale}/ once a translation exists here.
LOCALE_NAMES: dict[str, str] = {
    "fr": "French (France French, not Canadian)",
    "de": "German (Germany German)",
    "es": "Spanish (Spain Spanish, not Latin American)",
    "pt": "Portuguese — European Portuguese (Portugal), NOT Brazilian Portuguese",
    "sw": "Swahili (Kenyan Swahili)",
}
LOCALES = list(LOCALE_NAMES.keys())

BATCH_SIZE = 4
MAX_ATTEMPTS = 3

TRANSLATE_SYSTEM_PROMPT = """You are a professional sports-betting content translator for SifuFinds, an African sports betting comparison site written in UK English.

Translate the given article's title, excerpt, and body from UK English into {locale_name}. Rules:
- Preserve markdown formatting (headings, bold, tables, FAQ structure) exactly.
- Preserve every named entity (player names, team names, competitions, bookmaker brand names, currency codes) unchanged.
- Do not invent, add, or drop any factual claim — this is a translation, not a rewrite.
- Match the natural register of a sports journalist writing in {locale_name}, not a literal word-for-word translation.
- Keep the 18+/responsible gambling disclaimer line if present, translated appropriately.

Respond with ONLY valid JSON, no markdown fences:
{{"title": "...", "excerpt": "...", "body": "..."}}
"""


def _load_posts() -> list[dict]:
    data = json.loads(POSTS_JSON.read_text())
    return data["posts"] if isinstance(data, dict) else data


def _load_translations(locale: str) -> dict:
    path = TRANSLATIONS_DIR / f"{locale}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_translations(locale: str, translations: dict) -> None:
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = TRANSLATIONS_DIR / f"{locale}.json"
    path.write_text(json.dumps(translations, indent=2, ensure_ascii=False))


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _locale_state(state: dict, locale: str) -> dict:
    return state.setdefault(locale, {"processed": {}, "attempts": {}, "runs": 0})


def pick_locale(posts: list[dict], state: dict) -> str:
    """Locale with the biggest untranslated backlog, so a no-args run always
    makes progress on whichever locale needs it most."""
    slugs = {p["slug"] for p in posts}
    best_locale, best_backlog = LOCALES[0], -1
    for locale in LOCALES:
        translated = set(_load_translations(locale).keys())
        backlog = len(slugs - translated)
        if backlog > best_backlog:
            best_locale, best_backlog = locale, backlog
    return best_locale


def _pick_batch(posts: list[dict], translations: dict, locale_state: dict, batch_size: int) -> list[dict]:
    candidates = [
        p for p in posts
        if p["slug"] not in translations
        and locale_state["attempts"].get(p["slug"], 0) < MAX_ATTEMPTS
    ]
    return candidates[:batch_size]


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


def translate_post(post: dict, locale: str) -> dict | None:
    locale_name = LOCALE_NAMES[locale]
    system_prompt = TRANSLATE_SYSTEM_PROMPT.format(locale_name=locale_name)
    user_message = f"""TITLE: {post.get('title', '')}

EXCERPT: {post.get('excerpt', '')}

BODY:
{post.get('body', '')}
"""
    try:
        raw = ask_long(system_prompt, user_message)
    except AIProvidersExhausted as e:
        log("translate", "translate_post", "provider_exhausted", f"{locale}/{post.get('slug', '')}: {e}")
        return None

    try:
        data = json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        log("translate", "translate_post", "error",
            f"{locale}/{post.get('slug', '')}: could not parse translator response")
        return None

    if not data.get("title") or not data.get("body"):
        log("translate", "translate_post", "error",
            f"{locale}/{post.get('slug', '')}: translator response missing title/body")
        return None

    return {"title": data["title"], "excerpt": data.get("excerpt", ""), "body": data["body"]}


def run(locale: str | None = None, batch_size: int = BATCH_SIZE) -> int:
    if not POSTS_JSON.exists():
        print("blog/posts.json not found — nothing to do")
        return 0

    posts = _load_posts()
    state = _load_state()

    if locale is None:
        locale = pick_locale(posts, state)
    if locale not in LOCALES:
        print(f"Unknown locale '{locale}' — must be one of {LOCALES}")
        return 1

    locale_state = _locale_state(state, locale)
    locale_state["runs"] = locale_state.get("runs", 0) + 1

    translations = _load_translations(locale)
    total_needing = sum(1 for p in posts if p["slug"] not in translations)
    batch = _pick_batch(posts, translations, locale_state, batch_size)

    print(f"Country Localisation Agent — locale={locale} ({LOCALE_NAMES[locale]})")
    print(f"{total_needing} post(s) still untranslated, processing {len(batch)} this run")

    translated_count = 0
    for post in batch:
        slug = post["slug"]
        print(f"  → {slug}")
        result = translate_post(post, locale)
        if not result:
            # Distinguish infra failure (don't burn an attempt) from a bad
            # response we should eventually give up retrying — mirrors
            # agent_content_backfill.py's attempt-budget convention.
            locale_state["attempts"][slug] = locale_state["attempts"].get(slug, 0) + 1
            print(f"    ✗ translation failed — attempt {locale_state['attempts'][slug]}/{MAX_ATTEMPTS}")
            continue

        translations[slug] = result
        locale_state["processed"][slug] = {"processed_at": datetime.now(timezone.utc).isoformat()}
        translated_count += 1
        print(f"    ✓ translated ({len(result['body'])} chars)")

    if translated_count:
        _save_translations(locale, translations)
        log("translate", "run", "ok", f"{locale}: translated {translated_count} post(s)")
    else:
        log("translate", "run", "no_progress", f"{locale}: 0 post(s) translated this run")

    _save_state(state)
    print(f"\n✅ {translated_count} post(s) translated into {locale} this run. "
          f"Run gen_blog_post_pages.py --force to render the new pages.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locale", choices=LOCALES, default=None,
                         help="Locale to translate into. Default: auto-pick the locale with the biggest backlog.")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    return run(locale=args.locale, batch_size=args.batch_size)


if __name__ == "__main__":
    sys.exit(main())
