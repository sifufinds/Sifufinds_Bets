"""Read-only access to the real per-country bookmaker/market data already
embedded in assets/shared.js (COUNTRY_DATA, BOOKS) — the exact data the
site itself renders to visitors, so any agent using it for content
generation stays consistent with what's actually on the page instead of
inventing figures.

No JSON equivalent of this data exists anywhere in the repo (data/*.json
covers global bookmaker links and live bonus scrape results, but not the
per-country regulator/currency/payments/leagues grouping, or bonus copy
grouped by country rather than by bookmaker name) — this module parses the
JS object literals directly rather than duplicating the data a second time,
which would just create a second place for it to drift out of sync.

The parser is a generic (if minimal) JS-object-literal-to-JSON converter:
it correctly handles this file's mix of single- and double-quoted strings
(shared.js switches to double quotes specifically for values containing an
apostrophe, e.g. "Nigeria's No.1..."), escaped quotes, and unquoted keys.
It is read-only — nothing in this module ever writes back to shared.js.
"""
import json
import re
from pathlib import Path
from typing import Any

SHARED_JS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "shared.js"

_STRING_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
_UNQUOTED_KEY_RE = re.compile(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)")
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def _extract_balanced_block(varname: str, text: str, opener: str = "{") -> str | None:
    """Find `const <varname>={...}` (or `=[...]` with opener="[") and return
    the full block, respecting nesting and string contents (so a `}` inside
    a bonus description doesn't end the match early)."""
    closer = "}" if opener == "{" else "]"
    m = re.search(re.escape(varname) + r"\s*=\s*" + re.escape(opener), text)
    if not m:
        return None
    start = m.end() - 1
    depth = 0
    i = start
    in_str = False
    quote = ""
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                in_str = False
        else:
            if c in ("'", '"'):
                in_str = True
                quote = c
            elif c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        i += 1
    return None


def _js_object_to_json(js: str) -> str:
    """Convert a JS object literal to valid JSON text. Strings are pulled
    out to placeholders first so the unquoted-key regex never runs over
    string content (a value containing ", word:" would otherwise be
    misread as an object key)."""
    placeholders: list[str] = []

    def _stash(m: re.Match) -> str:
        raw = m.group(0)
        quote, content = raw[0], raw[1:-1]
        content = content.replace("\\'", "'") if quote == "'" else content.replace('\\"', '"')
        content = content.replace("\\", "\\\\").replace('"', '\\"')
        content = content.replace("\\\\\\\\", "\\\\")
        placeholders.append('"' + content + '"')
        return f"\x00{len(placeholders) - 1}\x00"

    skeleton = _STRING_RE.sub(_stash, js)
    skeleton = _UNQUOTED_KEY_RE.sub(r'\1"\2"\3', skeleton)
    skeleton = _TRAILING_COMMA_RE.sub(r"\1", skeleton)
    return re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], skeleton)


def _load_block(varname: str, opener: str = "{") -> Any:
    empty: Any = {} if opener == "{" else []
    if not SHARED_JS_PATH.exists():
        return empty
    text = SHARED_JS_PATH.read_text(encoding="utf-8")
    block = _extract_balanced_block(varname, text, opener)
    if not block:
        return empty
    try:
        return json.loads(_js_object_to_json(block))
    except (json.JSONDecodeError, ValueError):
        return empty


def load_country_data() -> dict[str, dict]:
    """{code: {name, flag, currency, symbol, region, regulator, about,
    payments[], leagues[]}} for all 33 countries — mirrors shared.js's
    COUNTRY_DATA exactly."""
    return _load_block("const COUNTRY_DATA")


def load_bookmakers() -> dict[str, list[dict]]:
    """{code: [bookmaker entries]} for all 33 countries — mirrors
    shared.js's BOOKS exactly. Each entry carries name/url/off/top/stars/
    min/lic/terms/pms among other display fields."""
    return _load_block("const BOOKS")


def load_casinos() -> list[dict]:
    """[casino entries] — mirrors shared.js's flat CASINOS list (powers
    /casino/). Not grouped by country: each entry's `min` is priced in one
    currency (₦, R, ...), which is the only per-market signal it carries."""
    return _load_block("const CASINOS", opener="[")


def casinos_for_country(code: str) -> list[dict]:
    """CASINOS entries priced in `code`'s own currency — the honest proxy
    for "this casino offer is aimed at this market". Symbol must be followed
    by a digit so e.g. South Africa's "R" can't match a "RWF..." price.
    Empty for most countries today (CASINOS only carries ₦ and R prices),
    which callers must treat as "no real casino data, don't write"."""
    symbol = load_country_data().get(code, {}).get("symbol", "")
    if not symbol:
        return []
    pattern = re.compile(re.escape(symbol) + r"\s?\d")
    return [c for c in load_casinos() if pattern.match(str(c.get("min", "")).strip())]
