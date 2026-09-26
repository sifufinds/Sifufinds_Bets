"""
RapidWombat Import Agent
Imports one article delivered by the RapidWombat webhook
(webhooks/rapidwombat.php → GitHub repository_dispatch →
.github/workflows/rapidwombat_import.yml) into blog/posts.json.

Like agent_sanity_sync.py, RapidWombat is an authoring source, not a new
rendering path: the output is one more entry in posts.json in the same dict
shape every other content agent produces, so gen_blog_post_pages.py and every
deploy gate (dedupe_slugs, sanitize_internal_links, JSON-LD, resources box,
18+/BeGambleAware footer, seo_check, compliance_check) apply unchanged.

Re-delivering the same article is idempotent: posts are keyed on
`rapidwombat-<article id>`, updated in place, and keep their original slug
and publish date so live URLs never move.

Usage:
  python3 agent_rapidwombat_import.py --payload-file payload.json
  python3 agent_rapidwombat_import.py --payload-file payload.json --dry-run

The payload is the webhook body ({id, title, content, cover_image}), with the
content either as plain `content` or gzip+base64 `content_gzip_b64` (what the
PHP endpoint forwards). Exit codes: 0 imported, 2 article rejected (bad or
unsafe content, do not retry), 1 unexpected error (safe to retry).
"""
import argparse
import base64
import gzip
import html
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from seo_meta import seo_meta_description  # noqa: E402

EXIT_REJECTED = 2
ID_PREFIX = "rapidwombat-"
MIN_WORDS = 300
MAX_SLUG_CHARS = 80
MAX_COVER_BYTES = 10 * 1024 * 1024
COVER_SIZE = (1200, 630)
DEFAULT_AUTHOR = "SifuFinds Editorial Team"
DEFAULT_CATEGORY = "betting"

# First match wins, checked against the lowercased title + opening of the body.
CATEGORY_KEYWORDS = [
    ("igaming", ("casino", "slot", "roulette", "blackjack", "aviator", "crash game", "jackpot")),
    ("transfers", ("transfer window", "transfer news", "signs for", "joins on loan")),
    ("basketball", ("basketball", "nba", "euroleague")),
    ("tennis", ("tennis", "wimbledon", "atp", "wta", "roland garros")),
    ("cricket", ("cricket", "ipl", "test match", "t20")),
    ("rugby", ("rugby", "springboks", "six nations")),
    ("boxing", ("boxing", "ufc", "heavyweight")),
    ("f1", ("formula 1", "formula one", "grand prix", "f1 ")),
    ("football", ("football", "premier league", "champions league", "afcon", "la liga",
                  "serie a", "bundesliga", "world cup", "npfl", "fkf")),
]

COUNTRY_TAGS = [
    "Nigeria", "Kenya", "Ghana", "South Africa", "Tanzania", "Uganda", "Zambia",
    "Ethiopia", "Ivory Coast", "Cameroon", "Senegal", "Rwanda", "Zimbabwe", "Malawi",
    "Mozambique", "Angola", "DR Congo", "Botswana", "Namibia", "Egypt", "Morocco",
    "Sierra Leone", "Liberia",
]

# Bookmakers with active review pages the resources box can link to.
BOOKMAKER_NAMES = ["SportyBet", "Betway", "1xBet", "22Bet", "Melbet", "betPawa", "Linebet"]

CATEGORY_STYLE = {
    "igaming": ("#7B2FBE", "🎰"),
    "football": ("#0B8043", "⚽"),
    "transfers": ("#0B8043", "🔁"),
    "basketball": ("#E8710A", "🏀"),
    "tennis": ("#9AA000", "🎾"),
    "cricket": ("#1A73E8", "🏏"),
    "rugby": ("#5F6368", "🏉"),
    "boxing": ("#C5221F", "🥊"),
    "f1": ("#C5221F", "🏎️"),
    "betting": ("#f2c464", "📊"),
}

_SAFE_URL_RE = re.compile(r"^(https?://|/|#|mailto:)", re.IGNORECASE)
_MD_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)]*)\)")


class ArticleRejected(ValueError):
    """The article itself is unusable. Retrying the same payload won't help."""


def decode_payload(payload: dict) -> dict:
    content = payload.get("content")
    if not content and payload.get("content_gzip_b64"):
        try:
            content = gzip.decompress(base64.b64decode(payload["content_gzip_b64"])).decode("utf-8")
        except (ValueError, OSError, UnicodeDecodeError) as exc:
            raise ArticleRejected(f"content_gzip_b64 could not be decoded: {exc}") from exc

    article_id = str(payload.get("id") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", article_id):
        raise ArticleRejected(f"invalid article id: {article_id!r}")
    title = re.sub(r"\s+", " ", str(payload.get("title") or "")).strip()
    if not title:
        raise ArticleRejected("article has no title")
    content = str(content or "").replace("\r\n", "\n").strip()
    if len(content.split()) < MIN_WORDS:
        raise ArticleRejected(f"article body under {MIN_WORDS} words — refusing thin content")

    cover = str(payload.get("cover_image") or "").strip()
    return {
        "id": article_id,
        "title": title,
        "content": content,
        "cover_image": cover if cover.lower().startswith(("http://", "https://")) else "",
    }


def _safe_link(match: re.Match) -> str:
    bang, text, url = match.group(1), match.group(2), match.group(3).strip()
    if not _SAFE_URL_RE.match(url) or any(c in url for c in '"<> '):
        return text  # unsafe/odd target (javascript:, quote injection) → keep the words only
    return f"{bang}[{text}]({url})"


def sanitize_markdown(body: str) -> str:
    """Make external markdown safe for gen_blog_post_pages.markdown_to_html(),
    which passes raw HTML and link targets straight through."""
    lines = body.split("\n")
    # Drop a leading "# Title" line: the page template already renders the <h1>.
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    body = "\n".join(lines).strip()
    body = body.replace("<", "&lt;").replace(">", "&gt;")
    return _MD_LINK_RE.sub(_safe_link, body)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(slug) > MAX_SLUG_CHARS:
        slug = slug[:MAX_SLUG_CHARS].rsplit("-", 1)[0]
    return slug or "article"


def unique_slug(base: str, taken: set[str]) -> str:
    slug, n = base, 2
    while slug in taken:
        slug = f"{base}-{n}"
        n += 1
    return slug


def plain_text(md: str) -> str:
    text = re.sub(r"<[^>]*>", "", html.unescape(md))
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`#>|]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def make_excerpt(body: str) -> str:
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if para and not para.startswith(("#", "|", "-", "*", "!")):
            return seo_meta_description(plain_text(para), 155)
    return seo_meta_description(plain_text(body), 155)


def detect_category(title: str, body: str) -> str:
    haystack = f" {title} {body[:1500]} ".lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(k in haystack for k in keywords):
            return category
    return DEFAULT_CATEGORY


def detect_tags(title: str, body: str) -> list[str]:
    haystack = f"{title} {body}"
    return [c for c in COUNTRY_TAGS if re.search(rf"\b{re.escape(c)}\b", haystack, re.IGNORECASE)][:6]


def detect_bookmaker(title: str, body: str) -> str:
    haystack = f"{title} {body}".lower()
    hits = [(haystack.find(b.lower()), b) for b in BOOKMAKER_NAMES if b.lower() in haystack]
    return min(hits)[1] if hits else ""


def build_post(article: dict, existing: dict | None, taken_slugs: set[str]) -> dict:
    body = sanitize_markdown(article["content"])
    category = detect_category(article["title"], body)
    color, icon = CATEGORY_STYLE.get(category, CATEGORY_STYLE[DEFAULT_CATEGORY])
    slug = existing["slug"] if existing else unique_slug(slugify(article["title"]), taken_slugs)
    return {
        "id": f"{ID_PREFIX}{article['id']}",
        "category": category,
        "title": article["title"],
        "slug": slug,
        "excerpt": make_excerpt(body),
        "body": body,
        "author": DEFAULT_AUTHOR,
        "published_at": (existing or {}).get("published_at") or datetime.now(timezone.utc).isoformat(),
        "image_color": color,
        "image_icon": icon,
        "tags": detect_tags(article["title"], body),
        "featured": False,
        "bookmaker_featured": detect_bookmaker(article["title"], body),
        "read_time": max(3, round(len(body.split()) / 200)),
        "_source": "rapidwombat",
    }


def save_cover_image(url: str, slug: str) -> str | None:
    """Download RapidWombat's cover image into assets/og/<slug>.png at the
    site's standard 1200x630 feature-image size. None on any failure, so the
    caller can fall back to the generated branded image."""
    import requests
    from PIL import Image
    from generate_blog_feature_image import OUT_DIR, _cover_fit

    try:
        resp = requests.get(url, timeout=20, stream=True)
        resp.raise_for_status()
        if not resp.headers.get("Content-Type", "").startswith("image/"):
            print(f"  ⚠  cover_image is not an image ({resp.headers.get('Content-Type')})")
            return None
        data = resp.raw.read(MAX_COVER_BYTES + 1, decode_content=True)
        if len(data) > MAX_COVER_BYTES:
            print("  ⚠  cover_image over 10 MB — skipped")
            return None
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:  # network, HTTP or decode failure — fall back, don't fail the import
        print(f"  ⚠  cover_image download failed: {exc}")
        return None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _cover_fit(img, *COVER_SIZE).save(OUT_DIR / f"{slug}.png", optimize=True)
    return f"/assets/og/{slug}.png"


def import_article(payload: dict, dry_run: bool = False) -> dict:
    from agent_sports_blog import load_posts, save_posts
    from generate_blog_feature_image import ensure_feature_image
    from utils.title_content_match import check_africa_framing

    article = decode_payload(payload)
    posts = load_posts()
    post_id = f"{ID_PREFIX}{article['id']}"
    existing_idx = next((i for i, p in enumerate(posts) if p.get("id") == post_id), None)
    existing = posts[existing_idx] if existing_idx is not None else None
    taken = {p.get("slug") for p in posts if p.get("id") != post_id}

    post = build_post(article, existing, taken)
    violation = check_africa_framing(post["title"], post["slug"], post["body"])
    if violation:
        raise ArticleRejected(f"title/content mismatch: {violation}")

    action = "update" if existing else "add"
    if dry_run:
        print(f"  {'~' if existing else '+'} would {action}: {post['title']!r} → /blog/{post['slug']}/")
        return post

    feature_image = None
    if article["cover_image"]:
        feature_image = save_cover_image(article["cover_image"], post["slug"])
    post["feature_image"] = feature_image or (existing or {}).get("feature_image") or ensure_feature_image(post)

    if existing is None:
        posts.insert(0, post)
    else:
        posts[existing_idx] = post
        # gen_blog_post_pages.py skips pages that already exist unless --force;
        # removing this one page makes a plain run rebuild just the updated post.
        (REPO_ROOT / "blog" / post["slug"] / "index.html").unlink(missing_ok=True)
    save_posts(posts)
    print(f"  ✓  {action}: {post['title']!r} → /blog/{post['slug']}/")
    return post


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-file", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ArticleRejected("payload is not a JSON object")
        post = import_article(payload, dry_run=args.dry_run)
    except (ArticleRejected, json.JSONDecodeError) as exc:
        print(f"  ✗  RapidWombat article rejected: {exc}")
        sys.exit(EXIT_REJECTED)

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"slug={post['slug']}\ntitle={post['title'].replace(chr(10), ' ')}\n")


if __name__ == "__main__":
    main()
