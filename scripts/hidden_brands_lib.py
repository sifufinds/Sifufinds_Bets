"""Hidden brands: config loading plus plain-text / markdown / JSON scrubbers.

A brand listed in data/hidden_brands.json must never be visible on the live
site. scripts/hide_brands.py applies these scrubbers (and the HTML scrubber in
hidden_brands_html.py) to the deploy copy of the site in CI, so repo source
files are never edited and un-hiding a brand is just removing it from the JSON.

Text is scrubbed in two passes, least destructive first:
  1. List removal: "Bet9ja, SportyBet and Betway" -> "SportyBet and Betway".
     Only applied when a neighbouring list item is itself a bookmaker name, so
     "Bet9ja, for example, offers..." is never mangled into "for example, ...".
  2. Sentence removal: any sentence still naming a hidden brand is dropped.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "hidden_brands.json"
SHARED_JS = ROOT / "assets" / "shared.js"

# Placeholder delimiters the HTML scrubber uses for atomic inline elements.
PH_OPEN, PH_CLOSE = "", ""
_PH_RE = re.compile(f"{PH_OPEN}(\\d+){PH_CLOSE}")

# Bookmaker names that are NOT hidden. Only used to recognise "a list of
# bookmakers" during list removal; shared.js names are added at load time.
_EXTRA_BOOKMAKERS = {
    "sportybet", "betway", "1xbet", "22bet", "melbet", "betika", "sportpesa",
    "paripesa", "betwinner", "helabet", "linebet", "fairpari", "premier bet",
    "betano", "10bet", "sportingbet", "wsb", "playabet", "mozzartbet",
    "odibets", "betpawa", "msport", "nairabet", "merrybet", "bangbet",
    "betlion", "parimatch", "stake", "bet365", "william hill", "pepeta",
    "gal sport", "betfair", "bwin", "unibet", "betsson", "888sport",
}
# Trailing qualifiers that don't change which bookmaker an item names.
_ITEM_SUFFIXES = {
    "nigeria", "kenya", "ghana", "sa", "south", "africa", "tanzania", "uganda",
    "zambia", "mz", "mozambique", "botswana", "namibia", "malawi", "zimbabwe",
    "casino", "sports", "sport", "ng", "ke", "gh", "za", "app", "online",
}
_CONNECTORS = ("and", "or", "&", "et", "und", "oder", "y", "o", "e", "ou", "und")
_ABBREVIATIONS = ("e.g.", "i.e.", "vs.", "no.", "approx.", "st.", "mr.", "dr.",
                  "p.", "fig.", "ca.", "z.b.", "p.ex.", "ex.", "etc.")
_SENT_SPLIT = re.compile(
    r"(?<=[.!?…])[\"”’)\]]*\s+(?=[\"“‘(¿¡\[" + PH_OPEN + r"]?[A-Z0-9À-ÖØ-Þ" + PH_OPEN + r"])"
)


@dataclass(frozen=True)
class HiddenBrands:
    names: tuple[str, ...]
    patterns: tuple[str, ...]
    domains: tuple[str, ...]
    regex: re.Pattern = field(repr=False)
    bookmakers: frozenset[str] = field(repr=False)

    def mentions(self, text: str | None) -> bool:
        if not text:
            return False
        if self.regex.search(text):
            return True
        low = text.lower()
        return any(d in low for d in self.domains)

    def _names_bookmaker(self, words: list[str]) -> bool:
        joined = " ".join(words)
        return joined in self.bookmakers or bool(self.regex.fullmatch(joined))

    def is_bookmaker_item(self, item: str) -> bool:
        """True when a list item names a bookmaker, allowing lead-in words
        ("such as SportyBet") and trailing prose ("SportyBet are popular")."""
        words = _clean_words(item)
        if not words:
            return False
        tail = _strip_suffixes(words)
        return any(self._names_bookmaker(words[:n]) or self._names_bookmaker(tail[-n:])
                   for n in (1, 2, 3) if n <= len(words))

    def is_brand_item(self, item: str) -> bool:
        """True when `item` is exactly a hidden brand plus country/product qualifiers."""
        words = _strip_suffixes(_clean_words(item))
        return 0 < len(words) <= 3 and bool(self.regex.fullmatch(" ".join(words)))


def _clean_words(item: str) -> list[str]:
    return re.sub(r"[^\w\s&+.-]", " ", item).lower().replace(" .", " ").split()


def _strip_suffixes(words: list[str]) -> list[str]:
    while len(words) > 1 and words[-1].strip(".") in _ITEM_SUFFIXES:
        words = words[:-1]
    return words


def load_config(path: Path = CONFIG_PATH) -> HiddenBrands:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"hidden brands: cannot read {path}: {exc}") from exc
    brands = raw.get("brands")
    if not isinstance(brands, list) or not brands:
        raise SystemExit(f"hidden brands: {path} has no 'brands' list")
    names, patterns, domains = [], [], []
    for b in brands:
        if not isinstance(b, dict) or not b.get("name") or not b.get("patterns"):
            raise SystemExit(f"hidden brands: bad entry in {path}: {b!r}")
        names.append(b["name"])
        patterns.extend(b["patterns"])
        domains.extend(d.lower() for d in b.get("domains", []))
    alternation = "|".join(f"(?:{p})" for p in patterns)
    regex = re.compile(rf"(?<![A-Za-z0-9])(?:{alternation})(?![A-Za-z])", re.I)
    return HiddenBrands(tuple(names), tuple(patterns), tuple(domains), regex,
                        frozenset(_known_bookmakers()))


def _known_bookmakers() -> set[str]:
    known = set(_EXTRA_BOOKMAKERS)
    try:
        src = SHARED_JS.read_text(encoding="utf-8")
    except OSError:
        return known
    for name in re.findall(r"name:'([^']+)'", src):
        words = name.lower().split()
        known.add(words[0])
        known.add(" ".join(words[:2]))
    return known


# ── sentences ────────────────────────────────────────────────────────────────

def split_sentences(text: str) -> list[str]:
    """Split on sentence ends, keeping each piece's trailing whitespace."""
    parts, start = [], 0
    for m in _SENT_SPLIT.finditer(text):
        head = text[start:m.start()].rstrip("\"”’)]").lower()
        if head.endswith(_ABBREVIATIONS):
            continue
        parts.append(text[start:m.end()])
        start = m.end()
    parts.append(text[start:])
    return [p for p in parts if p]


# ── list removal ─────────────────────────────────────────────────────────────

_ITEM_BREAK = re.compile(r"[,;:()\[\]—–!?]|\.(?=\s|$)|\s(?:" + "|".join(
    re.escape(c) for c in _CONNECTORS) + r")\s", re.I)


_CONNECTOR_RE = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, _CONNECTORS)) + r")(?!\w)", re.I)


def _item_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    left = 0
    for m in _ITEM_BREAK.finditer(text, 0, start):
        left = m.end()
    m = _ITEM_BREAK.search(text, end)
    right = m.start() if m else len(text)
    return left, right


def _extend_qualifiers(text: str, end: int) -> int:
    """Extend a brand mention over trailing qualifiers ("Bet9ja Ghana", "Supabets Casino")."""
    m = re.match(r"(?:\s+(?:" + "|".join(map(re.escape, sorted(_ITEM_SUFFIXES))) + r")(?![\w]))+",
                 text[end:], re.I)
    return end + (m.end() if m else 0)


def _sep_before(text: str, pos: int) -> re.Match | None:
    return re.search(r"(,\s*(?:(?:" + "|".join(map(re.escape, _CONNECTORS))
                     + r")\s+)?|\s+(?:" + "|".join(map(re.escape, _CONNECTORS))
                     + r")\s+|\s*/\s*)$", text[:pos], re.I)


def _sep_after(text: str, pos: int) -> re.Match | None:
    return re.match(r"(,\s*(?:(?:" + "|".join(map(re.escape, _CONNECTORS))
                    + r")\s+)?|\s+(?:" + "|".join(map(re.escape, _CONNECTORS))
                    + r")\s+|\s*/\s*)", text[pos:], re.I)


def _neighbour_item(text: str, start: int, end: int, expand: Callable[[str], str]) -> str:
    return expand(text[start:end]).strip(" \t\n\"'“”‘’*")


def remove_from_lists(text: str, hb: HiddenBrands,
                      expand: Callable[[str], str] = lambda s: s) -> str:
    """Drop hidden-brand items from inline enumerations of bookmakers.

    `expand` maps placeholder-bearing text back to readable text so the HTML
    scrubber can check whether a neighbouring <a>SportyBet</a> is a bookmaker.
    """
    for _ in range(50):  # each pass removes one item; bounded for safety
        changed = False
        for m in _brand_matches(text, hb, expand):
            new = _remove_one_item(text, m[0], m[1], hb, expand)
            if new is not None:
                text, changed = new, True
                break
        if not changed:
            return text
    return text


def _brand_matches(text: str, hb: HiddenBrands, expand: Callable[[str], str]):
    """Spans of hidden-brand mentions, including placeholders whose text names one."""
    spans = [(m.start(), m.end()) for m in hb.regex.finditer(text)]
    spans += [(m.start(), m.end()) for m in _PH_RE.finditer(text) if hb.mentions(expand(m.group(0)))]
    return sorted(spans)


def _remove_one_item(text, start, end, hb, expand):
    left, _ = _item_bounds(text, start, end)
    right = _extend_qualifiers(text, end)
    if not hb.is_brand_item(expand(text[start:right])):
        return None
    lead = text[left:start]  # "such as " etc. stays in the sentence
    # "(Bet9ja)" on its own
    lp, rp = text[:start].rstrip(), text[right:].lstrip()
    if not lead.strip() and lp.endswith("(") and rp.startswith(")"):
        b = len(text) - len(rp) + 1
        return (lp[:-1].rstrip() + text[b:]).replace(" ,", ",").replace(" .", ".")
    after = _sep_after(text, right)
    before = _sep_before(text, left) if not lead.strip() else None
    if after and before and _CONNECTOR_RE.search(after.group(1)) \
            and not _CONNECTOR_RE.search(before.group(1)):
        # "A, Hidden, and B" -> "A, and B": drop the comma before, keep the "and"
        return text[:before.start()] + text[right:]
    if after:
        nxt = right + after.end()
        _, nxt_r = _item_bounds(text, nxt, nxt)
        if hb.is_bookmaker_item(_neighbour_item(text, nxt, nxt_r, expand)):
            return text[:start] + text[nxt:]
    if before:
        prev_l, _ = _item_bounds(text, before.start(), before.start())
        if hb.is_bookmaker_item(_neighbour_item(text, prev_l, before.start(), expand)):
            word = _CONNECTOR_RE.search(before.group(1))
            head = text[:before.start()]
            if word:  # dropped the last item: its connector moves back one item
                comma = head.rfind(", ", max(0, prev_l - 2))
                if comma != -1:
                    head = head[:comma] + f" {word.group(1)} " + head[comma + 2:]
            return head + text[right:]
    return None


# ── plain text ───────────────────────────────────────────────────────────────

def scrub_text(text: str, hb: HiddenBrands,
               expand: Callable[[str], str] = lambda s: s) -> str:
    """Return `text` with every hidden-brand mention removed ('' if nothing survives)."""
    if not text or not _mentions_expanded(text, hb, expand):
        return text
    text = remove_from_lists(text, hb, expand)
    if not _mentions_expanded(text, hb, expand):
        return text
    kept = [s for s in split_sentences(text) if not _mentions_expanded(s, hb, expand)]
    out = "".join(kept)
    return out.strip() if not out.strip() else out.rstrip() + (" " if text.endswith(" ") else "")


def _mentions_expanded(text: str, hb: HiddenBrands, expand: Callable[[str], str]) -> bool:
    return hb.mentions(expand(text) if PH_OPEN in text else text)


# ── markdown ─────────────────────────────────────────────────────────────────

_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]*)[^)]*\)")
_MD_HEADING = re.compile(r"^(#{1,6})\s")


def scrub_markdown(md: str, hb: HiddenBrands) -> str:
    md = _MD_LINK.sub(lambda m: m.group(1) if hb.mentions(m.group(2)) else m.group(0), md)
    if not hb.mentions(md):
        return md
    lines, out, skip_level = md.split("\n"), [], 0
    i = 0
    while i < len(lines):
        line = lines[i]
        h = _MD_HEADING.match(line)
        if h and skip_level and len(h.group(1)) <= skip_level:
            skip_level = 0
        if skip_level:
            i += 1
            continue
        if h and hb.mentions(line):
            scrubbed = remove_from_lists(line, hb)
            if hb.mentions(scrubbed):
                skip_level = len(h.group(1))
                i += 1
                continue
            line = scrubbed
        if line.lstrip().startswith("|"):
            i = _scrub_md_table(lines, i, out, hb)
            continue
        if hb.mentions(line):
            prefix = re.match(r"^\s*(?:[-*+]|\d+\.)\s+|^\s*>\s*", line)
            p = prefix.group(0) if prefix else ""
            body = scrub_text(line[len(p):], hb)
            if not body.strip():
                i += 1
                continue
            line = p + body
        out.append(line)
        i += 1
    return "\n".join(out)


def _scrub_md_table(lines: list[str], i: int, out: list[str], hb: HiddenBrands) -> int:
    rows = []
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        rows.append(lines[i])
        i += 1
    cells = [r.strip().strip("|").split("|") for r in rows]
    header_sep = len(rows) > 1 and re.fullmatch(r"[\s|:-]+", rows[1])
    drop_cols = {c for c, v in enumerate(cells[0]) if hb.mentions(v)} if header_sep else set()
    for n, row in enumerate(cells):
        if n > 1 or not header_sep:
            if hb.mentions("|".join(row)) and not (drop_cols and not
                    hb.mentions("|".join(v for c, v in enumerate(row) if c not in drop_cols))):
                continue
        kept = [v for c, v in enumerate(row) if c not in drop_cols]
        if len(kept) > (1 if drop_cols else 0):
            out.append("| " + " | ".join(v.strip() for v in kept) + " |")
    return i


# ── JSON ─────────────────────────────────────────────────────────────────────

_IDENTITY_KEYS = ("name", "title", "headline", "brand", "brand_key", "bookmaker",
                  "slug", "url", "link", "href", "@id", "item", "logo_abbr_name")
_LIST_SEP_KEYS = ("keywords",)


def _identity(d: dict) -> list[str]:
    vals = []
    for k in _IDENTITY_KEYS:
        v = d.get(k)
        if isinstance(v, str):
            vals.append(v)
        elif isinstance(v, dict):
            vals += [x for x in (v.get("name"), v.get("@id"), v.get("url")) if isinstance(x, str)]
    return vals


def scrub_json(obj, hb: HiddenBrands, key: str | None = None):
    """Return a scrubbed copy of a JSON value (never mutates the input)."""
    if isinstance(obj, dict):
        return {k: scrub_json(v, hb, k) for k, v in obj.items() if not hb.mentions(k)}
    if isinstance(obj, list):
        kept = []
        for item in obj:
            if isinstance(item, dict) and any(hb.mentions(v) for v in _identity(item)):
                continue
            if isinstance(item, str) and len(item) <= 60 and hb.mentions(item):
                continue
            kept.append(scrub_json(item, hb, key))
        if kept and all(isinstance(x, dict) and isinstance(x.get("position"), int) for x in kept):
            kept = [{**x, "position": n} for n, x in enumerate(kept, 1)]
        return kept
    if isinstance(obj, str) and hb.mentions(obj):
        if key in _LIST_SEP_KEYS:
            return ", ".join(p.strip() for p in obj.split(",") if not hb.mentions(p))
        if "\n" in obj:
            return scrub_markdown(obj, hb)
        return scrub_text(obj, hb)
    return obj


_JSON_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def scrub_json_strings(src: str, hb: HiddenBrands) -> str:
    """Fallback for JSON that doesn't parse: scrub each string literal in place."""
    def fix(m: re.Match) -> str:
        if not hb.mentions(m.group(1)):
            return m.group(0)
        try:
            value = json.loads(m.group(0))
        except json.JSONDecodeError:
            return m.group(0)
        clean = scrub_markdown(value, hb) if "\n" in value else scrub_text(value, hb)
        return json.dumps(clean, ensure_ascii=False)
    return _JSON_STRING.sub(fix, src)
