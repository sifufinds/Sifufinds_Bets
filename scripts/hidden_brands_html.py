"""Hidden brands: HTML page scrubber (see hidden_brands_lib.py for the rules).

Removal units, most specific first, so a page keeps reading naturally:
  brand card / ad (a card that links to the brand)  -> whole card removed
  odds/comparison table column headed by the brand  -> column removed
  table row naming the brand                        -> row removed
  FAQ item whose question names the brand           -> whole Q&A removed
  heading naming the brand                          -> heading + its section
  short tag/chip/nav link ("📌 Bet9ja")             -> that element removed
  prose                                             -> list item or sentence removed
Anything still visible after that (a safety net) loses its nearest block.
"""
from __future__ import annotations

import base64
import html as html_lib
import json
import posixpath
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment, Doctype, NavigableString, Tag

from hidden_brands_lib import (PH_CLOSE, PH_OPEN, HiddenBrands, scrub_json, scrub_json_strings,
                               scrub_text)

SITE_HOST = "sifufinds.com"
INLINE = {"a", "abbr", "b", "bdi", "bdo", "cite", "code", "data", "dfn", "em", "i",
          "kbd", "mark", "q", "s", "samp", "small", "span", "strong", "sub", "sup",
          "time", "u", "var", "font", "br", "wbr"}
MEDIA = {"img", "svg", "video", "iframe", "picture", "canvas", "input", "select",
         "textarea", "audio", "object", "embed"}
STOP = {"html", "body", "main", "article", "head", "[document]"}
PROSE = {"p", "li", "td", "th", "dd", "dt", "blockquote", "figcaption", "summary",
         "h1", "h2", "h3", "h4", "h5", "h6", "caption", "label"}
HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
TEXT_ATTRS = ("alt", "title", "placeholder", "aria-label", "content", "value")
_CARD_CLASS = re.compile(r"^(?:bkcard|fc|sad|hbrand|op-card|bk-row)$|(?:^|[-_])(?:card|banner|ad|offer|promo|tile)$")
_FAQ_Q_CLASS = re.compile(r"faq-q|question|acc-q|acc-btn")
_FAQ_ITEM_CLASS = re.compile(r"faq-item|faq-entry|acc-item|accordion-item|qa-item")
_NAME_CLASS = re.compile(r"(?:^|-)(?:nm|name|title|brand)$")
_JS_DROP_LINE = re.compile(r"^\s*(?:\{.*\}\s*,?\s*(?://.*)?|//.*|/?\*.*)$")


@dataclass(frozen=True)
class Page:
    path: str                   # site-relative file path, e.g. "blog/x/index.html"
    hb: HiddenBrands
    stubbed: frozenset[str]     # site dirs replaced by redirect stubs, e.g. "blog/x/"

    @property
    def dir(self) -> str:
        return posixpath.dirname(self.path) + "/" if "/" in self.path else ""


# ── links ────────────────────────────────────────────────────────────────────

def resolve_href(href: str, page_dir: str) -> str | None:
    """Site-relative dir/file path for an internal href, None for external."""
    href = (href or "").strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    u = urlparse(href)
    if u.scheme in ("http", "https") or href.startswith("//"):
        if not u.netloc.lower().endswith(SITE_HOST):
            return None
        path = u.path
    else:
        path = posixpath.join("/" + page_dir, u.path) if u.path else "/" + page_dir
    path = posixpath.normpath(path).lstrip("/")
    if path in (".", ""):
        return ""
    if path.endswith("index.html"):
        path = path[: -len("index.html")]
    elif "." not in posixpath.basename(path):
        path += "/"
    return path


def is_hidden_href(href: str | None, page: Page) -> bool:
    if not href:
        return False
    if page.hb.mentions(href):
        return True
    return resolve_href(href, page.dir) in page.stubbed


# ── tree helpers ─────────────────────────────────────────────────────────────

def _classes(el: Tag) -> list[str]:
    return el.get("class") or [] if isinstance(el, Tag) else []


def _block_of(node) -> Tag | None:
    el = node if isinstance(node, Tag) else node.parent
    while el is not None and el.name in INLINE:
        el = el.parent
    return el


def _is_empty(el: Tag) -> bool:
    return (not el.get_text(strip=True) and el.find(MEDIA) is None
            and el.name not in MEDIA and not el.get("id") and el.find(id=True) is None)


def _remove(el: Tag) -> None:
    """Remove `el`, then any ancestors it leaves empty."""
    parent = el.parent
    el.decompose()
    while parent is not None and parent.name not in STOP and _is_empty(parent):
        nxt = parent.parent
        parent.decompose()
        parent = nxt


def _alive(node) -> bool:
    """False once a node (or an ancestor) has been removed from the tree."""
    try:
        return node.parent is not None and not getattr(node, "decomposed", False)
    except AttributeError:  # decompose() strips a NavigableString's attributes
        return False


def _text_hits(root, hb: HiddenBrands) -> list[NavigableString]:
    return [t for t in root.find_all(string=True)
            if not isinstance(t, (Comment, Doctype)) and t.parent is not None
            and t.parent.name not in ("script", "style", "title", "template")
            and hb.mentions(t)]


# ── removal units ────────────────────────────────────────────────────────────

def _entity_card(node, page: Page) -> Tag | None:
    el = node if isinstance(node, Tag) else node.parent
    depth = 0
    while el is not None and el.name not in STOP and depth < 8:
        if any(_CARD_CLASS.search(c) for c in _classes(el)) and len(el.get_text(" ")) < 2500:
            links = [a.get("href") for a in el.find_all("a", href=True)]
            if el.name == "a" and el.get("href"):
                links.append(el["href"])
            hidden = [h for h in links if is_hidden_href(h, page)]
            others = [h for h in links if not is_hidden_href(h, page) and urlparse(h).netloc
                      and not urlparse(h).netloc.endswith(SITE_HOST)]
            named = any(_NAME_CLASS.search(c) for n in el.find_all(class_=True)
                        for c in _classes(n) if page.hb.mentions(n.get_text(" ")))
            if (hidden or named) and not others:
                return el
        el, depth = el.parent, depth + 1
    return None


def _scrub_cards(soup, page: Page) -> None:
    hits = _text_hits(soup.body or soup, page.hb)
    hits += [a for a in soup.find_all("a", href=True) if is_hidden_href(a["href"], page)]
    for node in hits:
        if _alive(node):
            card = _entity_card(node, page)
            if card is not None:
                _remove(card)


def _scrub_tables(soup, page: Page) -> None:
    hb = page.hb
    for table in soup.find_all("table"):
        if not _alive(table):
            continue
        rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
        if not rows:
            continue
        header = rows[0] if rows[0].find("th") else None
        if header is not None:
            cells = header.find_all(["th", "td"], recursive=False)
            drop = [i for i, c in enumerate(cells) if i > 0 and hb.mentions(c.get_text(" "))]
            if drop and not any(c.get("colspan") for r in rows for c in r.find_all(["td", "th"], recursive=False)):
                for r in rows:
                    rc = r.find_all(["td", "th"], recursive=False)
                    for i in reversed(drop):
                        if i < len(rc):
                            rc[i].decompose()
                if len(header.find_all(["th", "td"], recursive=False)) < 2:
                    _remove(table)
                    continue
        for r in rows[1 if header is not None else 0:]:
            links = [a["href"] for a in r.find_all("a", href=True)]
            if hb.mentions(r.get_text(" ")) or any(is_hidden_href(h, page) for h in links):
                r.decompose()
        had_body = len(rows) > (1 if header is not None else 0)
        if had_body and not [r for r in table.find_all("tr") if r is not header]:
            _remove(table)  # every data row named a hidden brand


def _faq_container(node) -> Tag | None:
    el = node.parent
    in_question = False
    while el is not None and el.name not in STOP:
        if el.name in ("summary", "button") or any(_FAQ_Q_CLASS.search(c) for c in _classes(el)):
            in_question = True
        if in_question and (el.name == "details" or any(_FAQ_ITEM_CLASS.search(c) for c in _classes(el))):
            return el
        el = el.parent
    return None


def _remove_section(heading: Tag) -> None:
    level = HEADINGS[heading.name]
    sib = heading.next_sibling
    while sib is not None:
        nxt = sib.next_sibling
        if isinstance(sib, Tag) and sib.name in HEADINGS and HEADINGS[sib.name] <= level:
            break
        if isinstance(sib, Tag) and sib.find(list(HEADINGS)) is not None and \
                any(HEADINGS[h.name] <= level for h in sib.find_all(list(HEADINGS))):
            break
        sib.extract()
        sib = nxt
    _remove(heading)


def _scrub_links(soup, page: Page) -> None:
    for a in soup.find_all("a", href=True):
        if not _alive(a) or not is_hidden_href(a["href"], page):
            continue
        li = a.find_parent("li")
        block = _block_of(a.parent) if a.parent is not None else None
        if li is not None and li.get_text(strip=True) == a.get_text(strip=True):
            _remove(li)
        elif block is None or block.name not in PROSE or _classes(a) or \
                a.find_parent(class_=re.compile(r"breadcrumb|share|footer|nav|related|tags")):
            _remove(a)
        else:
            a.unwrap()


def _chip_of(node) -> Tag | None:
    """Outermost short inline element holding `node` inside a non-prose block,
    e.g. the <span>📌 Bet9ja</span> beside the date/author spans in a post header."""
    top, el = None, node.parent
    while el is not None and el.name in INLINE:
        top, el = el, el.parent
    if top is None or len(top.get_text(strip=True)) > 80:
        return None
    return top if el is None or el.name not in PROSE else None


def _scrub_prose(el: Tag, hb: HiddenBrands) -> None:
    """Remove hidden-brand list items / sentences from one block element."""
    for child in list(el.children):
        if isinstance(child, Tag) and child.name in INLINE and hb.mentions(child.get_text(" ")):
            if hb.is_brand_item(child.get_text(" ", strip=True)) or child.name == "a":
                child.replace_with(NavigableString(child.get_text()))
            else:
                _scrub_prose(child, hb)
                if _is_empty(child):
                    child.decompose()
    el.smooth()
    parts, holders = [], {}
    for child in el.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            parts.append(html_lib.escape(str(child), quote=False))
        else:
            n = len(holders)
            holders[n] = (str(child), child.get_text(" "))
            parts.append(f"{PH_OPEN}{n}{PH_CLOSE}")
    flat = "".join(parts)
    ph = re.compile(f"{PH_OPEN}(\\d+){PH_CLOSE}")
    expand = lambda s: html_lib.unescape(ph.sub(lambda m: holders[int(m.group(1))][1], s))  # noqa: E731
    new = scrub_text(flat, hb, expand)
    if new == flat:
        return
    rebuilt = ph.sub(lambda m: holders[int(m.group(1))][0], new)
    el.clear()
    for node in list(BeautifulSoup(rebuilt, "html.parser").contents):
        el.append(node)


def _scrub_text_nodes(soup, page: Page) -> None:
    hb = page.hb
    for node in _text_hits(soup.body or soup, hb):
        if not _alive(node):
            continue
        faq = _faq_container(node)
        if faq is not None:
            _remove(faq)
            continue
        chip = _chip_of(node)
        if chip is not None:
            _remove(chip)
            continue
        block = _block_of(node)
        if block is None or block.name in STOP:
            node.extract()
            continue
        _scrub_prose(block, hb)
        if block.name in HEADINGS and hb.mentions(block.get_text(" ")):
            _remove_section(block)
        elif _alive(block) and _is_empty(block):
            _remove(block)


def _safety_net(soup, page: Page) -> None:
    for node in _text_hits(soup.body or soup, page.hb):
        if not _alive(node):
            continue
        block = _block_of(node)
        if block is None or block.name in STOP:
            node.extract()
        else:
            _remove(block)
    for el in soup.find_all(True):
        if not _alive(el) or el.name == "script":
            continue
        for attr, val in list(el.attrs.items()):
            val = " ".join(val) if isinstance(val, list) else val
            if not isinstance(val, str) or not page.hb.mentions(val):
                continue
            if attr in ("href", "src", "srcset", "action") or attr.startswith("on"):
                _remove(el) if el.name not in STOP else el.attrs.pop(attr, None)
                break
            el[attr] = scrub_text(val, page.hb) if attr in TEXT_ATTRS else ""
            if not el[attr]:
                del el[attr]


# ── head, JSON-LD, scripts, comments ─────────────────────────────────────────

def scrub_js(src: str, hb: HiddenBrands) -> str:
    """Drop one-line object literals / comments naming a hidden brand."""
    if not hb.mentions(src):
        return src
    kept, in_block = [], False
    for ln in src.split("\n"):
        starts_in_block = in_block
        in_block = _block_state(ln, in_block)
        if not hb.mentions(ln):
            kept.append(ln)
        elif starts_in_block or (ln.lstrip().startswith("/*")):
            kept.append(_strip_brand_words(ln, hb))  # inside a /* */ comment
        elif _JS_DROP_LINE.match(ln):
            continue
        elif _JS_HIDDEN_CONST.match(ln):
            kept.append(_encode_hidden_const(ln))
        else:
            ln = _scrub_js_literals(ln, hb)
            comment = re.search(r"(?<![:'\"\\])//.*$", ln)
            if comment and hb.mentions(comment.group(0)):
                ln = ln[:comment.start()].rstrip()
            kept.append(ln)
    return "\n".join(kept)


def _block_state(line: str, in_block: bool) -> bool:
    """Track whether a /* */ comment is still open after this line (string-naive, fine for comments)."""
    for tok in re.findall(r"/\*|\*/", line):
        in_block = tok == "/*"
    return in_block


def _strip_brand_words(text: str, hb: HiddenBrands) -> str:
    out = hb.regex.sub("", text)
    for d in hb.domains:
        out = re.sub(re.escape(d), "", out, flags=re.I)
    return re.sub(r"(?<=\S) {2,}", " ", out)


_JS_HIDDEN_CONST = re.compile(r"^(\s*const HIDDEN_BRAND_(?:PATTERNS|DOMAINS)=)(\[.*\]);\s*$")
_JS_STR = r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\""
_JS_PAIR = re.compile(rf"\s*(?:{_JS_STR})\s*:\s*(?:{_JS_STR})\s*,?")
_JS_TOKEN = re.compile(rf"\s*(?:'[^'\s\\]*'|\"[^\"\s\\]*\")\s*,?")
_JS_LITERAL = re.compile(_JS_STR)


def _encode_hidden_const(line: str) -> str:
    """Ship shared.js's own hidden-brand list base64-encoded so no name appears in plain text."""
    m = _JS_HIDDEN_CONST.match(line)
    items = json.loads(m.group(2).replace("'", '"'))
    blob = base64.b64encode(json.dumps(items).encode()).decode()
    return f"{m.group(1)}JSON.parse(atob('{blob}'));"


def _scrub_js_literals(line: str, hb: HiddenBrands) -> str:
    """Remove brand map pairs ('HW':'x.net',) and array tokens ('x.co.za',); scrub prose strings."""
    line = _JS_PAIR.sub(lambda m: "" if hb.mentions(m.group(0)) else m.group(0), line)
    line = _JS_TOKEN.sub(lambda m: "" if hb.mentions(m.group(0)) else m.group(0), line)

    def prose(m: re.Match) -> str:
        lit = m.group(0)
        return lit[0] + scrub_text(lit[1:-1], hb) + lit[-1] if hb.mentions(lit) else lit
    return _JS_LITERAL.sub(prose, line)


def _scrub_scripts(soup, page: Page) -> None:
    for s in soup.find_all("script"):
        src = s.string
        if not src or not page.hb.mentions(src):
            continue
        if (s.get("type") or "").lower() == "application/ld+json":
            try:
                data = json.loads(src)
            except json.JSONDecodeError:  # already-broken JSON-LD: clean it without reformatting
                s.string = scrub_json_strings(src, page.hb)
                continue
            s.string = "\n" + json.dumps(scrub_json(data, page.hb), ensure_ascii=False, indent=2) + "\n"
        else:
            s.string = scrub_js(src, page.hb)


def _scrub_head(soup, page: Page) -> None:
    title = soup.title.get_text(strip=True) if soup.title else ""
    for link in soup.find_all("link", href=True):
        if is_hidden_href(link["href"], page):
            link.decompose()
    for meta in soup.find_all("meta", content=True):
        if not page.hb.mentions(meta["content"]):
            continue
        if (meta.get("name") or "").lower() == "keywords":
            meta["content"] = ", ".join(k.strip() for k in meta["content"].split(",")
                                        if not page.hb.mentions(k))
        else:
            meta["content"] = scrub_text(meta["content"], page.hb) or title


def _scrub_comments(soup, hb: HiddenBrands) -> None:
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if hb.mentions(c):
            c.extract()


# ── entry points ─────────────────────────────────────────────────────────────

def scrub_html(source: str, page: Page) -> str | None:
    """Scrubbed page HTML, or None when the page needs no change."""
    hb = page.hb
    if not hb.mentions(source) and not any(
            posixpath.basename(d.rstrip("/")) + "/" in source for d in page.stubbed):
        return None
    soup = BeautifulSoup(source, "html.parser")
    _scrub_comments(soup, hb)
    _scrub_head(soup, page)
    _scrub_scripts(soup, page)
    _scrub_cards(soup, page)
    _scrub_tables(soup, page)
    _scrub_links(soup, page)
    _scrub_text_nodes(soup, page)
    _safety_net(soup, page)
    out = str(soup)
    return out if out != source else None


def visible_leaks(source: str, page: Page) -> list[str]:
    """Hidden-brand mentions a visitor or crawler could still see on a page."""
    hb = page.hb
    if not hb.mentions(source):
        return []
    soup = BeautifulSoup(source, "html.parser")
    leaks = [f"text: {t.strip()[:80]}" for t in _text_hits(soup, hb)]
    leaks += [f"comment: {c.strip()[:60]}" for c in soup.find_all(string=lambda t: isinstance(t, Comment))
              if hb.mentions(c)]
    for el in soup.find_all(True):
        for attr, val in el.attrs.items():
            val = " ".join(val) if isinstance(val, list) else val
            if isinstance(val, str) and hb.mentions(val):
                leaks.append(f"<{el.name} {attr}>: {val[:80]}")
    for s in soup.find_all("script"):
        src = s.string or ""
        if (s.get("type") or "").lower() == "application/ld+json" and hb.mentions(src):
            leaks.append("json-ld: " + hb.regex.search(src).group(0) if hb.regex.search(src) else "json-ld")
        elif hb.mentions(src):
            m = hb.regex.search(src)
            leaks.append("inline script: " + (m.group(0) if m else "tracking domain"))
    return leaks


def page_heading_mentions(source: str, hb: HiddenBrands) -> bool:
    """Is this page *about* a hidden brand (its <title> or <h1> names one)?"""
    for pattern in (r"<title[^>]*>(.*?)</title>", r"<h1[^>]*>(.*?)</h1>"):
        m = re.search(pattern, source, re.I | re.S)
        if m and hb.mentions(re.sub(r"<[^>]+>", " ", m.group(1))):
            return True
    return False


def stub_html(target: str) -> str:
    """Redirect page served in place of a page about a hidden brand."""
    url = f"https://{SITE_HOST}/{target}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Page moved | SifuFinds</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url=/{target}">
<script>location.replace('/{target}');</script>
</head>
<body>
<p>This page has moved. <a href="/{target}">Continue to SifuFinds</a>.</p>
</body>
</html>
"""
