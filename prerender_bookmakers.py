"""Server-rendered fallback HTML for #bk-cards — real bookmaker data baked
into the initial page HTML instead of an empty div + a <noscript> "Enable
JavaScript" message.

Why this exists: found 2026-08-21 during an SEO/GEO audit that every
generator producing a #bk-cards listing (city pages, country pages, bonus
pages) shipped that div genuinely empty in the raw HTML, with the only
fallback content living inside <noscript> — invisible to any browser with
JS enabled, and of no help to a non-JS-executing crawler either once real
content exists outside it. Any crawler that doesn't run renderBooks()
(most AI crawlers, some non-Google search bots) saw zero bookmaker names,
offers, or odds on the exact pages built to rank/cite for that data,
confirmed via raw-vs-rendered word-count deltas of several hundred words
on sampled city pages.

The fix: render the same BOOKS data the client-side renderBooks() would,
directly into #bk-cards at generation time, sourced from the same real
data every visitor eventually sees (assets/shared.js's BOOKS, parsed via
agents/python/utils/site_data.py — never a second, hand-maintained copy).
renderBooks() already does `el.innerHTML = ...` unconditionally on load,
so this is pure progressive enhancement: a JS-enabled visitor sees no
difference (their browser overwrites this HTML within the same paint),
and a non-JS visitor or crawler now sees the real listing instead of a
placeholder message.

This intentionally does NOT replicate bookCard()'s async logo-image
loading (network-dependent, JS-driven canvas colour-sampling) or the
collapsible "More details" panel (interactive, adds little for a crawler
that already gets the core facts) — it renders the substantive, factual
content: name, offer, minimum deposit, sports count, licence, star
rating, payment methods, and the real (masked) claim link.
"""
from __future__ import annotations

import html
import os
import sys
from typing import Any

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "agents", "python"))

from utils.site_data import load_bookmakers  # noqa: E402

_BOOKS_CACHE: dict[str, list[dict[str, Any]]] | None = None


def _books() -> dict[str, list[dict[str, Any]]]:
    global _BOOKS_CACHE
    if _BOOKS_CACHE is None:
        _BOOKS_CACHE = load_bookmakers()
    return _BOOKS_CACHE


def _stars(n: int) -> str:
    n = max(0, min(int(n or 0), 5))
    return "★" * n + "☆" * (5 - n)


def _card_html(b: dict[str, Any], rank: int) -> str:
    name = html.escape(str(b.get("name", "")))
    abbr = html.escape(str(b.get("abbr", name[:2])))
    bg = html.escape(str(b.get("bg", "#333")))
    tc = html.escape(str(b.get("tc", "#fff")))
    tag = html.escape(str(b.get("tag", "")))
    off = html.escape(str(b.get("off", "")))
    min_dep = html.escape(str(b.get("min", "")))
    sports = html.escape(str(b.get("sports", "")))
    lic = html.escape(str(b.get("lic", "")))
    url = html.escape(str(b.get("url", "#")), quote=True)
    stars = _stars(b.get("stars", 0))
    badge = b.get("badge", "")
    badge_html = (
        '<span class="badge-new">NEW</span>' if badge == "new"
        else '<span class="badge-hot">HOT</span>' if badge == "hot"
        else '<span class="badge-nd">NO DEP</span>' if b.get("nodep") else ""
    )
    pms = "".join(
        f'<span class="pmc">{html.escape(str(p))}</span>' for p in (b.get("pms") or [])
    )
    top3 = " top3" if rank < 3 else ""
    nodep_cls = " nodep-card" if b.get("nodep") else ""
    return f'''<div class="bkcard{top3}{nodep_cls}">
  <div class="bk-main">
    <span class="bk-rk">#{rank + 1}</span>
    <div class="bk-logo" style="background:{bg};color:{tc};display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px">{abbr}</div>
    <div>
      <div class="bk-tag">{tag}</div>
      <div class="bk-nm">{name}{badge_html}</div>
      <div class="bk-off">{off}</div>
      <div class="bk-meta"><span>Min: {min_dep}</span><span>{sports} sports</span><span>{lic}</span></div>
    </div>
    <div class="bk-act">
      <div class="bk-stars">{stars}</div>
      <a class="gbtn{' gold' if b.get('nodep') else ''}" href="{url}" target="_blank" rel="noopener noreferrer sponsored">Claim Bonus →</a>
      <div class="tc-n">T&amp;Cs Apply · 18+</div>
    </div>
  </div>
  <div class="pm-row">{pms}</div>
</div>'''


def bookmaker_cards_html(country_code: str, fallback_message: str = "No bookmakers currently listed for this market.") -> str:
    """Real, server-rendered <div id="bk-cards"> contents for `country_code`
    (e.g. 'NG'), in the same default order BOOKS itself carries (matches
    the client's own 'Editors' Picks' default sort). Always returns
    genuine data already published elsewhere on the site — nothing here is
    invented for SEO purposes."""
    entries = _books().get(country_code.upper(), [])
    if not entries:
        return f'<p style="padding:16px;color:#666">{html.escape(fallback_message)}</p>'
    return "\n".join(_card_html(b, i) for i, b in enumerate(entries))
