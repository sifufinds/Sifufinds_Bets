#!/usr/bin/env python3
"""Regenerate llms-full.txt (llms.txt + one factual section per country).

Country facts (name, currency, regulator, payment rails, restricted flag) are
parsed live from COUNTRY_DATA in assets/shared.js, so adding a country needs
no hand-edit here. Also appends any country missing from llms.txt's country
list, so the two files cannot drift on coverage.
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LINE = re.compile(r"^\s{2}([A-Z]{2}):\{name:'((?:[^'\\]|\\.)*)'.*$")


def field(line, key):
    m = re.search(key + r":'((?:[^'\\]|\\.)*)'", line)
    return m.group(1).replace("\\'", "'") if m else ""


def parse_countries():
    out = []
    for line in (BASE / "assets" / "shared.js").read_text(encoding="utf-8").splitlines():
        m = LINE.match(line)
        if not m:
            continue
        pay = re.search(r"payments:\[(.*?)\]", line)
        out.append({
            "code": m.group(1),
            "name": m.group(2).replace("\\'", "'"),
            "currency": field(line, "currency"),
            "regulator": field(line, "regulator"),
            "restricted": "restricted:true" in line,
            "payments": re.findall(r"'((?:[^'\\]|\\.)*)'", pay.group(1)) if pay else [],
        })
    return out


def slug(name):
    return re.sub(r"[^a-z]+", "-", name.lower().replace("’", "")).strip("-")


def main():
    countries = parse_countries()
    if len(countries) < 30:
        sys.exit(f"parsed only {len(countries)} countries from shared.js; refusing to write")
    llms = (BASE / "llms.txt").read_text(encoding="utf-8")
    missing = [c for c in countries if f"best-betting-in-{slug(c['name'])}/" not in llms]
    if missing:
        add = "".join(
            f"- {c['name']}{' (informational only, restricted market)' if c['restricted'] else ''}: "
            f"https://sifufinds.com/best-betting-in-{slug(c['name'])}/\n" for c in missing)
        marker = "\n### Bookmaker Reviews"
        llms = llms.replace(marker, add + marker, 1)
        (BASE / "llms.txt").write_text(llms, encoding="utf-8")
    parts = [llms.rstrip(), "\n\n## Country Reference (generated from the live site data)\n"]
    for c in countries:
        status = ("Restricted market. SifuFinds lists no operators here; the page is informational only."
                  if c["restricted"] else "Bookmaker comparison page available.")
        parts.append(
            f"### {c['name']}\n- URL: https://sifufinds.com/best-betting-in-{slug(c['name'])}/\n"
            f"- Currency: {c['currency']}\n- Regulator: {c['regulator']}\n"
            f"- Common payment methods: {', '.join(c['payments'])}\n- Status: {status}\n")
    (BASE / "llms-full.txt").write_text("\n".join(parts), encoding="utf-8")
    print(f"llms-full.txt: {len(countries)} countries; added {len(missing)} to llms.txt")


if __name__ == "__main__":
    main()
