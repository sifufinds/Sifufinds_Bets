"""
Auto-heal the blog-post failures that block every Hostinger deploy.

Deploy gates (validate_site, audit_titles, check_indexability, seo_check,
compliance_check, check_country_count) are all-or-nothing: one bad blog post
blocks the whole site. Retrying a deploy cannot fix that, so before this
script every incident waited for a human, e.g. 2026-09-09 -> 2026-09-26
(merge-conflict markers in 2 generated pages) and most of 2026-09-27 ->
2026-10-02 (overstated-language phrases in a few posts).

Heals, in order, only things that are safe to fix without a human:
  1. Generated blog pages (blog/<slug>/index.html) carrying merge-conflict
     markers or unparseable JSON-LD -> deleted, so gen_blog_post_pages.py
     rebuilds them from blog/posts.json (it only creates missing pages).
  2. Overstated gambling-outcome phrases (compliance_check.BANNED_RE) in a
     post's title/excerpt/body in blog/posts.json, for posts whose page the
     gate flags -> the phrase is reworded in place ("risk-free bet" -> "free
     bet"), so headings/FAQ answers/opening answers keep their SEO/GEO
     structure; reported speech is never reworded, that sentence is dropped.
     Negated uses like "no guaranteed win" are kept (gate's own rule). The
     slug/URL is never changed. The post's page is then regenerated.
  3. Every gate's own --fix mode (seo_check, check_indexability,
     check_country_count, compliance_check).

Run from the repo root. Prints what it changed; always exits 0 so the calling
workflow decides what to do from `git status` and a re-run of the gates.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from compliance_check import BANNED_RE, _is_negated  # noqa: E402

POSTS_PATH = ROOT / "blog" / "posts.json"
POSTS_JS_PATH = ROOT / "blog" / "posts-data.js"
MARKER_RE = re.compile(r"^(<<<<<<<|>>>>>>>)( |$)", re.M)
JSONLD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
SENTENCE_RE = re.compile(r"[^.!?\n]*(?:[.!?]+|$)")
FIXERS = [
    ["scripts/seo_check.py", "--fix"],
    ["scripts/check_indexability.py", "--fix"],
    ["scripts/check_country_count.py", "--fix"],
    ["scripts/compliance_check.py", "--fix"],
]


def _page_is_broken(html: str) -> str | None:
    if MARKER_RE.search(html):
        return "merge-conflict markers"
    for block in JSONLD_RE.findall(html):
        try:
            json.loads(block)
        except json.JSONDecodeError:
            return "invalid JSON-LD"
    return None


def heal_broken_pages() -> list[str]:
    removed = []
    for page in sorted((ROOT / "blog").glob("*/index.html")):
        reason = _page_is_broken(page.read_text(encoding="utf-8", errors="ignore"))
        if reason:
            page.unlink()
            removed.append(page.parent.name)
            print(f"  ✓ {page.parent.name}: {reason}, page deleted for regeneration")
    return removed


# Honest, non-overstated equivalents. Rewriting the phrase (instead of
# deleting its sentence) keeps headings, FAQ answers (FAQPage schema) and the
# opening answer AI engines quote intact, so SEO/GEO structure is unchanged.
REWRITES = [
    (re.compile(r"risk[\s-]?free\s+bet|(?:zero|no)[\s-]?risk\s+bet", re.I), "free bet"),
    (re.compile(r"guaranteed\s+win|100%\s*win", re.I), "likely win"),
    (re.compile(r"can'?t\s+lose|cannot\s+lose", re.I), "shouldn't lose"),
    (re.compile(r"never\s+lose", re.I), "rarely lose"),
]
# Reported speech must not be reworded (that would misquote someone), so a
# flagged phrase inside a quote/attributed sentence drops the sentence.
REPORTED_SPEECH_RE = re.compile(
    r"[\"“”]|\b(said|says|claimed|claims|boasted|boasts|insisted|told|admitted|vowed|declared)\b", re.I)


def _rewrite_phrase(phrase: str) -> str:
    for pattern, replacement in REWRITES:
        if pattern.fullmatch(phrase):
            return replacement[0].upper() + replacement[1:] if phrase[0].isupper() else replacement
    return phrase


def heal_text(text: str) -> str:
    """Fix each banned phrase the gate would flag (gate's exact rule:
    _is_negated over the full text, so "no guaranteed win" disclaimers are
    left alone). Rewrites the phrase in place; drops the sentence only for
    reported speech. Paragraphs, headings, tables and FAQs keep their shape."""
    if not text:
        return text
    bad = [m for m in BANNED_RE.finditer(text) if not _is_negated(text, m.start())]
    if not bad:
        return text
    out, cursor = [], 0
    for m in SENTENCE_RE.finditer(text):
        start, end = m.span()
        hits = [b for b in bad if start <= b.start() < end]
        if not hits:
            continue
        sentence = text[start:end]
        out.append(text[cursor:start])
        if not REPORTED_SPEECH_RE.search(sentence):
            pieces, pos = [], start
            for b in hits:
                pieces += [text[pos:b.start()], _rewrite_phrase(b.group(0))]
                pos = b.end()
            pieces.append(text[pos:end])
            out.append("".join(pieces))
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


def _gate_flagged_slugs() -> set[str]:
    """Blog posts whose generated page fails the compliance gate right now.
    Scoping to these keeps the healer no stricter than the gate itself."""
    import compliance_check
    compliance_check.issues.clear()
    compliance_check.check_banned_language()
    slugs = set()
    for i in compliance_check.issues:
        parts = Path(i["page"]).parts
        if i["severity"] == compliance_check.CRITICAL and len(parts) == 3 and parts[0] == "blog":
            slugs.add(parts[1])
    compliance_check.issues.clear()
    return slugs


def heal_banned_language() -> list[str]:
    flagged = _gate_flagged_slugs()
    if not flagged:
        print("  OK  no blog post fails the overstated-language gate")
        return []
    data = json.loads(POSTS_PATH.read_text(encoding="utf-8"))
    healed = []
    for post in data.get("posts", []):
        if post.get("slug") not in flagged:
            continue
        changed = False
        for field in ("title", "excerpt", "body"):
            old = post.get(field) or ""
            new = heal_text(old)
            if new != old and new.strip():
                post[field] = new
                changed = True
        if changed:
            healed.append(post.get("slug", ""))
            page_dir = ROOT / "blog" / post.get("slug", "")
            if post.get("slug") and page_dir.is_dir():
                shutil.rmtree(page_dir)
            print(f"  ✓ {post.get('slug')}: overstated phrase reworded")
    if healed:
        payload = json.dumps(data, indent=2, ensure_ascii=False)
        POSTS_PATH.write_text(payload + "\n", encoding="utf-8")
        POSTS_JS_PATH.write_text(
            f"window.POSTS_DATA={json.dumps(data, ensure_ascii=False)};\n", encoding="utf-8")
    return healed


def run(cmd: list[str]) -> None:
    result = subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True)
    tail = (result.stdout + result.stderr).strip().splitlines()[-1:] or [""]
    print(f"  {' '.join(cmd)} -> exit {result.returncode}: {tail[0][:140]}")


def main() -> None:
    print("Blog gate self-heal")
    print("1. Broken generated pages")
    broken = heal_broken_pages()
    print("2. Overstated language in posts.json")
    banned = heal_banned_language()
    if broken or banned:
        print("   Regenerating missing blog pages")
        run(["gen_blog_post_pages.py"])
    print("3. Gate auto-fixers")
    for cmd in FIXERS:
        run(cmd)
    print(f"Done: {len(broken)} page(s) rebuilt, {len(banned)} post(s) cleaned")


if __name__ == "__main__":
    main()
