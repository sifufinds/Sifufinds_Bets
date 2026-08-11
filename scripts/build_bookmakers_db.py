#!/usr/bin/env python3
"""Build data/bookmakers.json — the canonical brand x country bookmaker facts
database (Sifufinds Testing Database, Phase 1: consolidation).

Problem this solves: bookmaker facts currently live in four places that
disagree with each other and none of them carries a country dimension:
  - agents/python/agent_brand_reviews.py    BRANDS (19 brands, static)
  - agents/python/agent_telegram_offers.py  BRANDS (same 19, drifted copy)
  - brands/data.json                        11 brands, daily-scraped bonus copy
  - gen_bk_reviews.py                        BOOKMAKERS (3 brands, richest —
                                              genuinely country-specific payment
                                              lists for the single-country ones)
This script merges all four (plus data/bookmaker_links.json for review-page
status and agents/python/utils/affiliate_links.py's BRAND_SLUGS for the
canonical slug and generate_country_pages.py's COUNTRIES for currency/regulator
reference) into one file, keyed by canonical slug then by country code.

It does NOT invent verification. A payment-methods list that was written once
and applied across five countries (e.g. Sportybet's global list mixing OPay
with M-Pesa) is exactly the unverified generalisation the Sifufinds rulebook
(Section 3, Section 13) warns against, so it stays at brand level tagged
"unverified_multi_country_claim" instead of being copied into every country
row as if it had been checked per market. Only single-country brands — where
there is no ambiguity about which country a claim refers to — get their
existing claims promoted into that one country's record, and even then tagged
"documented" (carried from past editorial research) rather than "verified"
(independently confirmed) or "tested" (first-hand SifuFinds testing).

Re-run this whenever the source files change; it always rebuilds from scratch
so it never accumulates stale merges.
"""
import ast
import json
import os
import re
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REVIEW_SCORECARD_WEIGHTS = {
    "sports_markets": 0.20,
    "odds_experience": 0.15,
    "payments": 0.15,
    "withdrawals": 0.15,
    "bonuses": 0.10,
    "mobile_experience": 0.10,
    "customer_support": 0.05,
    "licensing_trust": 0.05,
    "africa_market_fit": 0.05,
}

AFRICA_FIT_DIMENSIONS = [
    "country_availability",
    "local_currencies",
    "local_payment_methods",
    "mobile_accessibility",
    "african_sports_coverage",
    "local_customer_support",
    "local_promotions",
    "withdrawal_convenience",
    "local_regulatory_fit",
]


def extract_top_level(filepath: str, name: str):
    """Statically extract a top-level `name = <literal>` (or annotated
    assignment) from a Python file via ast.literal_eval, without importing
    the module. Several source files import llm.py / network clients at
    module scope, so a real import is neither safe nor necessary here — we
    only need the literal data, not any behaviour the module defines."""
    with open(filepath, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.target is not None:
            targets = [node.target]
        else:
            continue
        for t in targets:
            if isinstance(t, ast.Name) and t.id == name:
                return ast.literal_eval(node.value)
    raise ValueError(f"Could not find top-level `{name}` in {filepath}")


def load_json(relpath: str):
    with open(os.path.join(BASE, relpath), encoding="utf-8") as f:
        return json.load(f)


def normalize_slug(name: str) -> str:
    s = re.sub(r"\s+africa$", "", name.strip().lower())
    return re.sub(r"[^a-z0-9]", "", s)


def load_sources():
    brand_reviews = extract_top_level(
        os.path.join(BASE, "agents/python/agent_brand_reviews.py"), "BRANDS"
    )
    telegram_offers = extract_top_level(
        os.path.join(BASE, "agents/python/agent_telegram_offers.py"), "BRANDS"
    )
    bk_reviews = extract_top_level(os.path.join(BASE, "gen_bk_reviews.py"), "BOOKMAKERS")
    brand_slugs = extract_top_level(
        os.path.join(BASE, "agents/python/utils/affiliate_links.py"), "BRAND_SLUGS"
    )
    countries_ref = extract_top_level(os.path.join(BASE, "generate_country_pages.py"), "COUNTRIES")
    scraped = load_json("brands/data.json").get("brands", {})
    links = load_json("data/bookmaker_links.json").get("bookmakers", [])
    return {
        "brand_reviews": brand_reviews,
        "telegram_offers": telegram_offers,
        "bk_reviews": bk_reviews,
        "brand_slugs": brand_slugs,
        "countries_ref": countries_ref,
        "scraped": scraped,
        "links": links,
    }


def canonical_slug(name: str, brand_slugs: dict) -> str:
    key = normalize_slug(name)
    return brand_slugs.get(key, key)


def country_name_to_code(countries_ref: dict) -> dict:
    return {info["name"]: code for code, info in countries_ref.items()}


def empty_country_record() -> dict:
    return {
        "availability": {"status": "not_yet_researched", "evidence": None, "last_checked": None},
        "payment_methods": {
            "deposit": [],
            "withdrawal": [],
            "status": "not_yet_researched",
            "note": "Not independently verified. Check the operator's current terms and registration page before depositing.",
        },
        "min_deposit": {"value": None, "status": "not_yet_researched"},
        "min_withdrawal": {"value": None, "status": "not_yet_researched"},
        "withdrawal_time": {
            "value": None,
            "status": "not_tested",
            "note": "First-hand SifuFinds testing not yet performed for this market.",
        },
        "sports_markets": {"value": None, "status": "not_yet_researched"},
        "licence": {"value": None, "status": "not_yet_researched"},
        "africa_fit": {
            "score": None,
            "breakdown": {dim: None for dim in AFRICA_FIT_DIMENSIONS},
            "status": "not_yet_scored",
        },
    }


def new_scorecard() -> dict:
    return {
        cat: {"score": None, "weight": weight} for cat, weight in REVIEW_SCORECARD_WEIGHTS.items()
    }


def promote_single_country_claims(country_rec: dict, legacy: dict, source_label: str):
    """A single-country brand's global claims are unambiguous — carry them
    into that one country's record as "documented" (researched editorial
    content), not "verified" (nobody independently cross-checked it yet)."""
    if legacy.get("payment_methods"):
        country_rec["payment_methods"] = {
            "deposit": list(legacy["payment_methods"]),
            "withdrawal": list(legacy["payment_methods"]),
            "status": "documented",
            "note": f"Carried from {source_label}; not yet independently re-verified.",
        }
    elif legacy.get("payments"):
        country_rec["payment_methods"] = {
            "deposit": list(legacy["payments"]),
            "withdrawal": list(legacy["payments"]),
            "status": "documented",
            "note": f"Carried from {source_label}; not yet independently re-verified.",
        }
    if legacy.get("min_deposit"):
        country_rec["min_deposit"] = {"value": legacy["min_deposit"], "status": "documented"}
    if legacy.get("min_withdrawal"):
        country_rec["min_withdrawal"] = {"value": legacy["min_withdrawal"], "status": "documented"}
    if legacy.get("sports") or legacy.get("sports_count"):
        country_rec["sports_markets"] = {
            "value": legacy.get("sports") or legacy.get("sports_count"),
            "status": "documented",
        }
    if legacy.get("licence"):
        country_rec["licence"] = {"value": legacy["licence"], "status": "documented"}
    country_rec["availability"] = {
        "status": "claimed",
        "evidence": f"Single-country brand per {source_label}.",
        "last_checked": None,
    }


def build_brand(slug: str, name: str, sources: dict, name_to_code: dict) -> dict:
    brand_reviews_rec = next(
        (b for b in sources["brand_reviews"] if canonical_slug(b["name"], sources["brand_slugs"]) == slug),
        None,
    )
    telegram_rec = next(
        (b for b in sources["telegram_offers"] if canonical_slug(b["name"], sources["brand_slugs"]) == slug),
        None,
    )
    scraped_rec = next(
        (v for k, v in sources["scraped"].items() if canonical_slug(k, sources["brand_slugs"]) == slug),
        None,
    )
    bk_review_rec = next(
        (b for b in sources["bk_reviews"] if canonical_slug(b["name"], sources["brand_slugs"]) == slug),
        None,
    )
    link_rec = next(
        (b for b in sources["links"] if canonical_slug(b["brand_name"], sources["brand_slugs"]) == slug),
        None,
    )

    countries_claimed = (brand_reviews_rec or telegram_rec or {}).get("countries", [])
    countries_codes = [name_to_code[c] for c in countries_claimed if c in name_to_code]

    countries = {code: empty_country_record() for code in countries_codes}

    single_country = len(countries_codes) == 1
    if single_country and brand_reviews_rec:
        promote_single_country_claims(
            countries[countries_codes[0]], brand_reviews_rec, "agent_brand_reviews.py (legacy static data)"
        )
    if bk_review_rec and bk_review_rec.get("country_page"):
        code = bk_review_rec.get("country_code")
        if code:
            countries.setdefault(code, empty_country_record())
            promote_single_country_claims(
                countries[code],
                {
                    "payment_methods": bk_review_rec.get("payments"),
                    "min_deposit": bk_review_rec.get("min_deposit"),
                    "min_withdrawal": bk_review_rec.get("min_withdrawal"),
                    "sports": bk_review_rec.get("sports"),
                    "licence": bk_review_rec.get("licence"),
                },
                "gen_bk_reviews.py (existing review page copy)",
            )

    official_url = link_rec.get("official_url") if link_rec else None
    review_page_status = link_rec.get("status") if link_rec else "missing"
    review_page_href = None
    if link_rec and link_rec.get("status") == "active":
        review_page_href = f"bookmakers/{slug}/"

    multi_country_claims = None
    if not single_country and brand_reviews_rec:
        multi_country_claims = {
            "payment_methods": brand_reviews_rec.get("payment_methods"),
            "min_deposit": brand_reviews_rec.get("min_deposit"),
            "licence": brand_reviews_rec.get("licence"),
            "status": "unverified_multi_country_claim",
            "note": (
                "This brand claims multiple countries; the fields above were "
                "written once and applied across all of them without "
                "per-country confirmation. Do not treat as true for any "
                "single market until researched into that market's own "
                "row under countries."
            ),
        }
        for code in countries_codes:
            countries[code]["availability"] = {
                "status": "claimed",
                "evidence": "Listed in agent_brand_reviews.py's countries array; not independently re-verified per market.",
                "last_checked": None,
            }

    return {
        "name": name,
        "slug": slug,
        "official_url": official_url,
        "review_page": review_page_href,
        "review_page_status": review_page_status,
        "identity": {
            "founded": (brand_reviews_rec or {}).get("founded"),
            "hq": (brand_reviews_rec or {}).get("hq"),
        },
        "countries": countries,
        "multi_country_claims": multi_country_claims,
        "review_scorecard": new_scorecard(),
        "overall_rating": None,
        "africa_fit_overall": None,
        "legacy_rating": {
            "stars_1to5": (brand_reviews_rec or telegram_rec or {}).get("stars"),
            "source": "agent_brand_reviews.py / agent_telegram_offers.py static data — subjective, predates the Sifufinds weighted scorecard methodology, kept for reference only.",
        },
        "legacy": {
            "brand_reviews_static": brand_reviews_rec,
            "telegram_offers_static": telegram_rec,
            "scraped_daily": scraped_rec,
            "review_page_copy": bk_review_rec,
            "bookmaker_links_entry": link_rec,
        },
    }


def main():
    sources = load_sources()
    name_to_code = country_name_to_code(sources["countries_ref"])

    all_names = {}
    for b in sources["brand_reviews"]:
        all_names[canonical_slug(b["name"], sources["brand_slugs"])] = b["name"]
    for b in sources["telegram_offers"]:
        all_names.setdefault(canonical_slug(b["name"], sources["brand_slugs"]), b["name"])
    for name in sources["scraped"]:
        all_names.setdefault(canonical_slug(name, sources["brand_slugs"]), name)
    for b in sources["bk_reviews"]:
        all_names.setdefault(canonical_slug(b["name"], sources["brand_slugs"]), b["name"])
    for b in sources["links"]:
        all_names.setdefault(canonical_slug(b["brand_name"], sources["brand_slugs"]), b["brand_name"])
    for slug in set(sources["brand_slugs"].values()):
        all_names.setdefault(slug, slug)

    brands = {}
    for slug, name in sorted(all_names.items()):
        brands[slug] = build_brand(slug, name, sources, name_to_code)

    countries_reference = {
        code: {
            "name": info["name"],
            "currency": info["currency"],
            "symbol": info["symbol"],
            "regulator": info.get("regulator"),
            "common_payment_rails": info.get("payments", []),
            "note": "common_payment_rails describes methods generally used for online payments in this country per generate_country_pages.py — it is NOT a claim that any specific bookmaker supports them.",
        }
        for code, info in sources["countries_ref"].items()
    }

    out = {
        "_schema_version": 1,
        "_comment": (
            "Canonical brand x country bookmaker facts database — the "
            "Sifufinds Testing Database. Single source of truth intended to "
            "replace the overlapping brand schemas in agent_brand_reviews.py, "
            "agent_telegram_offers.py, brands/data.json and "
            "data/bookmaker_links.json. See CLAUDE.md's 'Sifufinds Testing "
            "Database' section for the verification-status model this file "
            "follows (not_yet_researched -> documented -> claimed -> "
            "verified -> tested)."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/build_bookmakers_db.py",
        "countries_reference": countries_reference,
        "brands": brands,
    }

    out_path = os.path.join(BASE, "data/bookmakers.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {out_path}")
    print(f"  {len(brands)} brands, {len(countries_reference)} countries")
    single = sum(1 for b in brands.values() if b["multi_country_claims"] is None and b["countries"])
    multi = sum(1 for b in brands.values() if b["multi_country_claims"] is not None)
    print(f"  {single} single-country brands (claims promoted to country level)")
    print(f"  {multi} multi-country brands (claims kept at brand level, unverified per market)")


if __name__ == "__main__":
    main()
