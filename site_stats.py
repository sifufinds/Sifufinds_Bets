#!/usr/bin/env python3
"""Canonical country-count helpers — single source of truth so "N African
countries" copy across every generator (and any guard script) never drifts
out of sync from the real data again.

Parses COUNTRY_DATA directly out of assets/shared.js rather than hardcoding
a number anywhere. Adding a country to COUNTRY_DATA and re-running the page
generators (plus scripts/check_country_count.py --fix for hand-authored
pages) is the ONLY step needed to update this number site-wide.

See CLAUDE.md's "Country Count Is Continuously Self-Healing" standing rule.
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SHARED_JS = os.path.join(BASE_DIR, 'assets', 'shared.js')

_ENTRY_RE = re.compile(r'(?:^|\n)\s*([A-Z]{2}):\{')
_RESTRICTED_RE = re.compile(r'restricted:true')
_CURRENCY_RE = re.compile(r"currency:'([A-Z]{3})'")


def _country_data_block() -> str:
    with open(_SHARED_JS, encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'const COUNTRY_DATA=\{(.*?)\n\};', text, re.DOTALL)
    if not m:
        raise RuntimeError('Could not find COUNTRY_DATA block in assets/shared.js')
    return m.group(1)


def total_country_count() -> int:
    """Every country SifuFinds has a page for, including the restricted/
    informational-only markets. This is the number for "SifuFinds covers N
    African countries" style copy — a true geographic-coverage claim."""
    return len(_ENTRY_RE.findall(_country_data_block()))


def promotable_country_count() -> int:
    """Countries with at least the possibility of a real bookmaker listing
    (excludes markets flagged restricted:true, where online betting is
    banned/heavily restricted and SifuFinds lists no bookmaker or affiliate
    link by design). Use this number for copy that implies commercial
    bookmaker coverage — "N licensed bookmakers", partnership/outreach
    pitches, keyword-research agent targeting — never total_country_count()
    for those, or the claim becomes false for the restricted markets."""
    block = _country_data_block()
    return total_country_count() - len(_RESTRICTED_RE.findall(block))


def distinct_currency_count() -> int:
    """Distinct currency codes across all countries (several share a
    currency — XOF/XAF each cover multiple countries — so this is NOT the
    same as total_country_count())."""
    return len(set(_CURRENCY_RE.findall(_country_data_block())))


if __name__ == '__main__':
    print(f'Total countries:      {total_country_count()}')
    print(f'Promotable countries: {promotable_country_count()}')
    print(f'Distinct currencies:  {distinct_currency_count()}')
