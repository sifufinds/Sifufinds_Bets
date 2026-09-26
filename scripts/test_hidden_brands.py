"""Tests for the hidden-brands scrubber. Run: python3 scripts/test_hidden_brands.py
(also collected by pytest if it's installed)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hidden_brands_html import Page, scrub_html, visible_leaks  # noqa: E402
from hidden_brands_lib import load_config, scrub_json, scrub_markdown, scrub_text  # noqa: E402

HB = load_config()


def test_list_item_removed_keeps_sentence():
    out = scrub_text("Top bookmakers such as Bet9ja, SportyBet, Betway, Hollywoodbets, and 1xBet.", HB)
    assert out == "Top bookmakers such as SportyBet, Betway, and 1xBet."


def test_last_item_moves_connector_back():
    assert scrub_text("SportyBet, Betway and Hollywoodbets offer it.", HB) == "SportyBet and Betway offer it."


def test_non_list_sentence_dropped_not_mangled():
    out = scrub_text("Bet9ja, for example, is offering 2.50. Betway has 2.40.", HB)
    assert out == "Betway has 2.40."


def test_parenthetical_brand_removed():
    assert scrub_text("Nigeria at 6.00 (Bet9ja) is value.", HB) == "Nigeria at 6.00 is value."


def test_generic_words_untouched():
    text = "SuperSport broadcasts the PSL. Your first bet matters."
    assert scrub_text(text, HB) == text


def test_json_drops_entities_and_renumbers():
    data = {"bookmakers": {"Bet9ja": {}, "Betway": {}},
            "itemListElement": [{"name": "Hollywoodbets", "position": 1}, {"name": "Betway", "position": 2}],
            "tags": ["Bet9ja", "Nigeria"], "keywords": "odds, bet9ja promo, tips"}
    out = scrub_json(data, HB)
    assert out == {"bookmakers": {"Betway": {}}, "itemListElement": [{"name": "Betway", "position": 1}],
                   "tags": ["Nigeria"], "keywords": "odds, tips"}
    assert "Bet9ja" in data["bookmakers"]  # input not mutated


def test_markdown_table_row_and_heading_section():
    md = "## Bet9ja Review\nAll about it.\n## Odds\n| Bookie | Odd |\n| --- | --- |\n| Bet9ja | 1.9 |\n| 1xBet | 2.0 |"
    out = scrub_markdown(md, HB)
    assert "Bet9ja" not in out and "| 1xBet | 2.0 |" in out and "## Odds" in out


def test_html_units():
    html = """<html><head><title>AFCON odds</title><meta name="description" content="Odds at Bet9ja. Tips inside."></head>
<body><div class="post-meta"><span>📅 June 1</span><span>📌 Bet9ja</span></div>
<table><thead><tr><th>Market</th><th>Bet9ja</th><th>1xBet</th></tr></thead>
<tbody><tr><td>Winner</td><td>2.0</td><td>2.1</td></tr></tbody></table>
<div class="bkcard"><div class="bk-nm">Hollywoodbets</div><a href="https://www.hollywoodbets.net">Claim</a></div>
<p>Use <a href="../../bookmakers/bet9ja/">Bet9ja</a>, <a href="../../bookmakers/sportybet/">SportyBet</a> and Betway.</p>
</body></html>"""
    page = Page("blog/x/index.html", HB, frozenset({"bookmakers/bet9ja/"}))
    out = scrub_html(html, page)
    assert out and not visible_leaks(out, page)
    assert "📅 June 1" in out and "Winner" in out and "<th>1xBet</th>" in out
    assert "Tips inside." in out and "bkcard" not in out
    assert "SportyBet</a> and Betway." in out


if __name__ == "__main__":
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print(f"  ok  {name}")
    print(f"{len(tests)} passed")
