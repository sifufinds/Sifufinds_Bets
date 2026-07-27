#!/usr/bin/env python3
"""Generate a unique per-post feature image for any blog post.

Every blog post previously shared one identical sitewide og-image.png (or a
generic stock category photo on the blog listing page) — the same gap the
2026-07-19 GEO audit flagged for bookmaker reviews (see
generate_review_og_images.py). This script closes that gap for the general
content pipeline (agent_sports_blog.py, gen_blog_post_pages.py NEW_POSTS)
so every post gets its own 1200x630 image.

Per the 2026-07-26 standing rule ("use a free image of the player/team/person
you're talking about as the feature image"), this now tries a real photo
first: it pulls candidate subject names from the post's own tags (populated
by the content pipeline with the specific players/clubs/teams a post is
about) and looks each up via utils/player_photo.find_entity_image(), which
searches sports news outlets (BBC/Sky/ESPN) and social platforms first, then
falls back to Wikimedia Commons — see that module's docstring for the full
reasoning and the copyright tradeoff that source order carries. Candidates
are filtered through _looks_like_entity_candidate() first so a generic tag
("Transfers", "World Cup 2026", "Value Bets") never even reaches an image
search, where a loose query could return an unrelated but plausible-looking
photo. When a photo is found it's composited into the same on-brand layout
(kicker, headline, wordmark) as a full-bleed hero behind a gradient scrim.
When no subject photo can be confirmed — a generic tips/odds/bonus post with
no named player or club — it falls back to the original icon-card design
driven by image_color/image_icon, exactly as before.

Output goes to assets/og/{slug}.png, which gen_blog_post_pages.py already
picks up automatically for <meta property="og:image"> / twitter:image. Since
LinkedIn's share preview (and Facebook, X, Telegram) is built entirely from
those same OG tags, one generated image covers the blog post hero, the
blog listing card (via the `feature_image` field written back to
posts.json), and every social share target with no extra work.

Usage:
  python3 scripts/generate_blog_feature_image.py <slug>       # one post
  python3 scripts/generate_blog_feature_image.py --all-missing  # backfill every post lacking one
"""
from __future__ import annotations

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent
POSTS_JSON = ROOT / "blog" / "posts.json"
OUT_DIR = ROOT / "assets" / "og"

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "agents" / "python"))
from utils.player_photo import (  # noqa: E402
    fetch_entity_photo, looks_like_person_name, qualify_entity_query, search_news_photo,
)

_PHOTO_HEADERS = {
    "User-Agent": "SifuFindsBot/1.0 (https://sifufinds.com; contact: kai.s.manyeh@gmail.com)",
}

# Content is authored on macOS but rendered on ubuntu-latest GitHub Actions
# runners too (breaking_news.yml runs agent_sports_blog.py there several
# times a day) — font paths must resolve on both. The CI workflow installs
# fonts-dejavu-core + fonts-noto-color-emoji so the Linux paths below exist;
# these lists still fall through gracefully if a path is ever missing.
FONT_CANDIDATES = {
    "black": [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "regular": [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}
EMOJI_FONT_CANDIDATES = [
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto-color-emoji/NotoColorEmoji.ttf",
]
# Color emoji fonts are bitmap-strike formats that only load at specific
# native pixel sizes ("invalid pixel size" otherwise) — try the largest
# strikes first, then thumbnail down to whatever size the layout needs.
EMOJI_TRY_SIZES = [160, 136, 128, 109, 96, 64, 48]

W, H = 1200, 630
WHITE = (255, 255, 255)
GOLD = (245, 197, 66)

CATEGORY_LABELS = {
    "football": "Football",
    "sportnews": "Sport News",
    "transfers": "Transfers",
    "betting": "Betting Tips",
    "igaming": "iGaming",
    "basketball": "Basketball",
    "tennis": "Tennis",
    "cricket": "Cricket",
    "rugby": "Rugby",
    "boxing": "Boxing",
    "f1": "Formula 1",
    "world-cup": "World Cup 2026",
    "worldcup2026": "World Cup 2026",
    "review": "Bookmaker Review",
}


def _category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, (category or "Blog").replace("-", " ").title())


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = (h or "#1a6b35").lstrip("#")
    if len(h) != 6:
        h = "1a6b35"
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _blend(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))  # type: ignore[return-value]


def _darken(c: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, round(v * factor)) for v in c)  # type: ignore[return-value]


def _gradient_bg(base: tuple[int, int, int]) -> Image.Image:
    dark = _darken(base, 0.6)
    light = _blend(base, WHITE, 0.22)
    top = Image.new("RGB", (W, H), dark)
    bottom = Image.new("RGB", (W, H), light)
    mask = Image.new("L", (W, H))
    mask.putdata([int(255 * ((x + y) / (W + H))) for y in range(H) for x in range(W)])
    return Image.composite(bottom, top, mask)


def _font(weight: str, size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES[weight]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def _load_emoji_font() -> tuple[ImageFont.FreeTypeFont, int] | None:
    for path in EMOJI_FONT_CANDIDATES:
        if not Path(path).exists():
            continue
        for size in EMOJI_TRY_SIZES:
            try:
                return ImageFont.truetype(path, size), size
            except OSError:
                continue
    return None


def _emoji_image(emoji: str, target_size: int) -> Image.Image | None:
    """Renders a color emoji glyph, or None if no color emoji font is
    available on this machine (caller falls back to a plain glyph)."""
    loaded = _load_emoji_font()
    if loaded is None:
        return None
    font, native_size = loaded
    canvas = Image.new("RGBA", (native_size + 20, native_size + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        draw.text((10, 10), emoji, font=font, embedded_color=True)
    except Exception:
        return None
    bbox = canvas.getbbox()
    if not bbox:
        return None
    cropped = canvas.crop(bbox)
    cropped.thumbnail((target_size, target_size), Image.LANCZOS)
    return cropped


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == max_lines - 1 and current:
            continue
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


def build_image(title: str, category: str, image_color: str, image_icon: str) -> Image.Image:
    base = _hex_to_rgb(image_color)
    img = _gradient_bg(base)
    draw = ImageDraw.Draw(img, "RGBA")

    # Decorative translucent ring motif — same brand device used across every
    # generated OG image (bookmaker reviews, countries) for visual consistency.
    ring_center = (W - 150, 130)
    for r, alpha in [(240, 14), (185, 18), (130, 22)]:
        draw.ellipse(
            [ring_center[0] - r, ring_center[1] - r, ring_center[0] + r, ring_center[1] + r],
            outline=(*GOLD, alpha), width=3,
        )

    # White card holding the category emoji
    card_w, card_h = 340, 340
    card_x, card_y = 90, (H - card_h) // 2
    draw.rounded_rectangle(
        [card_x + 8, card_y + 12, card_x + card_w + 8, card_y + card_h + 12],
        radius=26, fill=(0, 0, 0, 70),
    )
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=26, fill=WHITE,
    )
    emoji_img = _emoji_image(image_icon or "📰", 190)
    if emoji_img is not None:
        ex = card_x + (card_w - emoji_img.width) // 2
        ey = card_y + (card_h - emoji_img.height) // 2
        img.paste(emoji_img, (ex, ey), emoji_img)
    else:
        # No color emoji font on this machine (e.g. a CI runner missing
        # fonts-noto-color-emoji) — fall back to the category's initial
        # letter on a coloured badge instead of leaving the card blank.
        f_fallback = _font("black", 140)
        letter = _category_label(category)[:1].upper() or "S"
        lb = draw.textbbox((0, 0), letter, font=f_fallback)
        lx = card_x + (card_w - (lb[2] - lb[0])) // 2 - lb[0]
        ly = card_y + (card_h - (lb[3] - lb[1])) // 2 - lb[1]
        draw.text((lx, ly), letter, font=f_fallback, fill=base)

    # Headline block
    text_x = card_x + card_w + 65
    text_w = W - text_x - 55

    f_kicker = _font("bold", 24)
    f_headline = _font("black", 46)
    f_sub = _font("regular", 26)

    draw.text((text_x, 90), f"SIFUFINDS  ·  {_category_label(category).upper()}", font=f_kicker, fill=GOLD)

    lines = _wrap_text(draw, title, f_headline, text_w, max_lines=4)
    y = 145
    for line in lines:
        draw.text((text_x, y), line, font=f_headline, fill=WHITE)
        y += 58

    draw.text((text_x, y + 14), "Betting tips & odds for African bettors", font=f_sub, fill=(230, 235, 232))

    # Bottom-left wordmark for brand consistency across every generated image
    f_brand = _font("bold", 24)
    draw.text((60, H - 62), "SIFUFINDS", font=f_brand, fill=GOLD)
    draw.text((60, H - 34), "Africa's Betting Comparison Platform", font=_font("regular", 18), fill=(200, 210, 205))

    return img.convert("RGB")


# The tag-candidate filter (_looks_like_entity_candidate and its supporting
# blocklists) lives in feature_image_tag_filter.py, not here — that module is
# pure-stdlib (only `re`) so scripts/validate_site.py's pre-deploy CHECK 4 can
# import it directly without pulling in Pillow, which the deploy workflow
# never installs. Importing it here too keeps every existing call site in
# this file (and backfill_feature_photos.py / audit_feature_images.py, which
# import _looks_like_entity_candidate from *this* module) working unchanged.
from feature_image_tag_filter import (  # noqa: E402
    _BLOCKED_TAG_WORDS,
    _COMPETITION_STRUCTURE_WORDS,
    _GENERIC_TAG_WORDS,
    _ORG_AND_COMPETITION_WORDS,
    _is_competition_reference,
    _looks_like_entity_candidate,
    _looks_like_womens_context,
    _tokenize,
)


def _looks_like_full_person_name(tag: str) -> bool:
    """True for a tag shaped like a full person name (2+ capitalized words,
    e.g. 'Bruno Fernandes', 'Erling Haaland') — used only to *prioritise*
    candidate order below, never to reject anything.

    Root cause this exists for (found 2026-07-27 auditing feature images):
    a transfer post tagged ['Transfers', 'Juventus', 'Bruno Fernandes',
    'Chelsea', 'Napoli'] tried 'Juventus' first (plain tag order) and
    search_news_photo('Juventus') surfaced an old Cristiano Ronaldo photo —
    a real, verifiable footballer, so every existing safety check (Wikipedia
    entity-context, gender-match) passed, yet the person shown had nothing
    to do with this specific story. A bare club/country query has no way to
    prefer 'a photo relevant to this article' over 'any photo tagged with
    this club', whereas a full person name is inherently much less
    ambiguous. Since transfer headlines are almost always structured around
    a named player, trying full-name tags first (before single-word club/
    country tags reachable at the same position) fixes the common case
    without changing anything for posts that only ever had club/country
    tags to begin with."""
    words = tag.split()
    return len(words) >= 2 and all(w[0].isupper() for w in words if w[0].isalpha())


def _candidate_priority(tag: str) -> int:
    """Lower sorts first. Three tiers, least to most ambiguous as a photo
    search subject:
      0. Full person name (2+ capitalized words) — 'Bruno Fernandes'.
      1. Single-word mononym shaped like a real surname — 'Barcola',
         'Rodri' (looks_like_person_name's stricter single-word rule
         already excludes short all-caps club acronyms here — see below).
      2. Everything else — bare clubs/countries/acronyms ('PSG', 'Juventus',
         'Real Madrid', 'Nigeria').

    Tier 2 exists because a bare club/country query is the least specific
    possible search: a news search for "PSG" doesn't reliably find *this
    article's* subject, it finds *any* article that happens to mention PSG
    at all. Found live 2026-07-27: a 'PSG Want £145m for Barcola' post's
    first-tried tag was 'PSG' (single-word, tried before 'Barcola' later in
    the same tag list under plain tag order), and search_news_photo('PSG')
    surfaced an unrelated Sky Sports article about a completely different
    player (Yan Diomande) that happened to also mention PSG in passing.
    Trying the more specific single-word surname first avoids this."""
    if _looks_like_full_person_name(tag):
        return 0
    if looks_like_person_name(tag):
        return 1
    return 2


def _subject_candidates(post: dict, limit: int = 8) -> list[str]:
    """Candidate player/team/person names to try for a real photo, sourced
    entirely from the post's own tags — the content pipeline already
    populates these with the specific players/clubs/teams a post is about
    (see agent_sports_blog.py — real examples: ['Real Madrid', 'Marc
    Cucurella', 'Cape Verde'], ['NBA', 'Knicks', 'New York']). Filtered
    through _looks_like_entity_candidate() so a purely generic/descriptive
    tag never reaches an image search. Sorted by _candidate_priority (stable
    — relative order within each tier is unchanged) so a specific named
    person is always tried before a bare club/country/acronym tag, since a
    person is the least ambiguous, least likely-to-mismatch kind of subject
    for a news-image search — see _candidate_priority's docstring for the
    two distinct incidents this avoids.
    """
    candidates: list[str] = []
    for tag in post.get("tags", []) or []:
        tag = (tag or "").strip()
        if tag and tag not in candidates and _looks_like_entity_candidate(tag):
            candidates.append(tag)
    candidates.sort(key=_candidate_priority)
    return candidates[:limit]


def _download_photo(url: str, timeout: int = 8) -> Image.Image | None:
    try:
        req = urllib.request.Request(url, headers=_PHOTO_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return Image.open(io.BytesIO(r.read())).convert("RGB")
    except Exception:
        return None


def verified_entity_photo(
    name: str, womens_context: bool = False, sport: str = "", other_tags: list[str] | None = None,
) -> str | None:
    """Only returns a photo URL once Wikipedia's own page independently
    confirms `name` is a real sports subject (fetch_entity_photo's
    entity-context check) — then prefers a nicer/more current photo of that
    exact confirmed name from the news/social tier, falling back to the
    Wikipedia image itself.

    Deliberately does NOT trust search_news_photo() on its own the way an
    earlier version of this function did: a bulk backfill run (2026-07-26)
    on ~200 published posts caught this the hard way — an unrestricted tag
    like "Tactical Trends" or a bookmaker name excluded elsewhere in the
    pipeline ("Betika") still matched *something* via news/social image
    search (a same-titled but unrelated stats chart; a different
    bookmaker's logo entirely), because that tier only checks that every
    word of the query appears in a result's title, with no check that the
    query is a real entity in the first place. Wikipedia's own summary/
    search API doing that verification first is a free, already-proven
    safety net (used for player photos since before this feature existed)
    — requiring it to pass before ever trusting the louder, noisier
    news-search tier turns "returns *something* for almost any string" into
    "returns nothing unless the subject is real," which is the property
    this whole feature depends on (a wrong photo is worse than none).

    Also runs `name` through qualify_entity_query() first, which rewrites a
    bare country tag ('Morocco') to its unambiguous men's-side Wikipedia
    title ('Morocco national football team') by default — closing the
    gender-ambiguity gap that let a Men's FIFA ranking post surface a
    Morocco WOMEN's World Cup celebration photo (2026-07-27): a bare country
    name has no way to signal which side a search should be about, and both
    Wikipedia's search fallback and the news-image search will happily
    return either. `womens_context`, sourced from the whole post (see
    feature_image_tag_filter._looks_like_womens_context) rather than this
    one candidate name, flips
    that default to the women's title instead — added after a second,
    distinct incident (2026-07-27, WAFCON) where the men's-side default
    itself was the bug: a post about the Women's Africa Cup of Nations
    tagged ['WAFCON', 'Nigeria', 'Morocco'] resolved 'Nigeria' to the men's
    team because nothing told this function the post was about the women's
    tournament in the first place.

    Also passes `sport` (the post's own category) through so a bare country
    tag resolves to the correct sport's national team — see
    qualify_entity_query's docstring for the cricket/basketball incident
    this closes (a bare country tag defaulting to football regardless of
    what sport the post was actually about).

    `other_tags` (the post's remaining candidate tags) is passed to
    search_news_photo as extra query context — needed for a nickname-style
    candidate that's also an ordinary English phrase: 'Black Stars' (Ghana's
    football nickname) collided with an unrelated BBC feature titled
    "Moments that made Britain's black stars" (2026-07-27), since that
    result legitimately contains both words too. Adding a co-occurring tag
    like 'Ghana' to the actual search query text (not just a post-hoc title
    filter) steers DuckDuckGo's own relevance ranking toward the correct
    football-specific results instead."""
    query = qualify_entity_query(name, womens_context=womens_context, sport=sport)
    wiki_url = fetch_entity_photo(query, sport=sport)
    if not wiki_url:
        return None
    context = [t for t in (other_tags or []) if t and t != name]
    return search_news_photo(query, context_clubs=context, sport=sport) or wiki_url


def find_subject_photo(post: dict) -> Image.Image | None:
    """Tries each candidate subject in turn, returns the first real,
    Wikipedia-verified photo that resolves and downloads (see
    verified_entity_photo), or None if the post has no identifiable
    player/team/person (e.g. a generic tips or bonus post)."""
    womens_context = _looks_like_womens_context(
        post.get("title", ""), post.get("excerpt", ""),
        *(post.get("tags", []) or []),
    )
    sport = post.get("category", "")
    candidates = _subject_candidates(post)
    for name in candidates:
        other_tags = [t for t in candidates if t != name]
        url = verified_entity_photo(name, womens_context, sport, other_tags)
        if not url:
            continue
        photo = _download_photo(url)
        if photo is not None:
            return photo
    return None


def _cover_fit(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize + crop to fill a w x h box with no distortion, the same idea
    as CSS `background-size: cover`.

    Wikipedia infobox photos are almost always portrait-oriented headshots
    with the face in the upper third — a dead-centre vertical crop (the
    naive `background-position: center` equivalent) reliably cropped straight
    through the subject's chin/neck instead of showing their face (caught by
    actually rendering a test image before shipping this, not just reading
    the code). Horizontal cropping still centres, since landscape sources
    don't have the same top-heavy bias."""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_h, new_w = h, round(h * src_ratio)
    else:
        new_w, new_h = w, round(w / src_ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = round((new_h - h) * 0.12) if new_h > h else 0
    return resized.crop((left, top, left + w, top + h))


def build_image_with_photo(title: str, category: str, image_color: str, photo: Image.Image) -> Image.Image:
    """Same on-brand kicker/headline/wordmark language as build_image(), but
    with a real subject photo as the full-bleed hero behind a bottom-heavy
    gradient scrim, instead of the generic icon card — used whenever
    find_subject_photo() confirms a real player/team photo for the post."""
    base = _hex_to_rgb(image_color)
    photo_fit = _cover_fit(photo, W, H)
    dark = _darken(base, 0.25)

    # Bottom-heavy scrim so headline/wordmark stay legible over any photo —
    # same putdata-mask compositing idea as _gradient_bg above.
    dark_layer = Image.new("RGB", (W, H), dark)
    mask = Image.new("L", (W, H))
    mask.putdata([min(230, round(35 + 195 * (y / H) ** 1.6)) for y in range(H) for _ in range(W)])
    img = Image.composite(dark_layer, photo_fit, mask)
    draw = ImageDraw.Draw(img, "RGBA")

    # Kicker pill, top-left — echoes the tag-pill language used on the
    # generic branded card elsewhere in the pipeline (utils/social_image.py).
    f_kicker = _font("bold", 24)
    kicker_text = f"SIFUFINDS  ·  {_category_label(category).upper()}"
    pad_x, pad_y = 20, 10
    kicker_w = draw.textlength(kicker_text, font=f_kicker)
    pill = (60, 50, 60 + kicker_w + pad_x * 2, 50 + 24 + pad_y * 2)
    draw.rounded_rectangle(pill, radius=22, fill=(*dark, 210))
    draw.text((pill[0] + pad_x, pill[1] + pad_y - 2), kicker_text, font=f_kicker, fill=GOLD)

    # Headline, bottom-anchored over the darkest part of the scrim
    f_headline = _font("black", 54)
    pad_x2 = 72
    lines = _wrap_text(draw, title, f_headline, W - pad_x2 * 2, max_lines=3)
    line_h = 62
    y = H - 100 - len(lines) * line_h
    for line in lines:
        draw.text((pad_x2, y), line, font=f_headline, fill=WHITE)
        y += line_h

    draw.text((pad_x2, H - 40), "SIFUFINDS.COM", font=_font("bold", 22), fill=GOLD)

    return img


def generate_feature_image(post: dict) -> str | None:
    """Generate assets/og/{slug}.png for one post. Returns the site-relative
    URL on success, None on failure (never raises — a broken image must not
    block publishing the post itself)."""
    slug = post.get("slug")
    if not slug:
        return None
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        photo = find_subject_photo(post)
        if photo is not None:
            print(f"  ✓ using a real subject photo as the feature image for {slug}")
            img = build_image_with_photo(
                title=post.get("title", ""),
                category=post.get("category", ""),
                image_color=post.get("image_color", "#1a6b35"),
                photo=photo,
            )
        else:
            img = build_image(
                title=post.get("title", ""),
                category=post.get("category", ""),
                image_color=post.get("image_color", "#1a6b35"),
                image_icon=post.get("image_icon", "📰"),
            )
        out_path = OUT_DIR / f"{slug}.png"
        img.save(out_path, "PNG", optimize=True)
        return f"/assets/og/{slug}.png"
    except Exception as e:
        print(f"  ⚠ feature image generation failed for {slug}: {e}", file=sys.stderr)
        return None


def ensure_feature_image(post: dict) -> str | None:
    """Generate the feature image only if it doesn't already exist. Used by
    the auto-heal step in gen_blog_post_pages.py so re-running never
    regenerates images for posts that already have one."""
    slug = post.get("slug")
    if not slug:
        return None
    existing = OUT_DIR / f"{slug}.png"
    if existing.exists():
        return f"/assets/og/{slug}.png"
    return generate_feature_image(post)


def backfill_all_missing() -> None:
    with open(POSTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    posts = data.get("posts", [])
    updated = 0
    for post in posts:
        slug = post.get("slug")
        if not slug or (OUT_DIR / f"{slug}.png").exists():
            continue
        url = generate_feature_image(post)
        if url:
            post["feature_image"] = url
            updated += 1
            print(f"  ✓ {slug}")
    if updated:
        with open(POSTS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Generated {updated} feature image(s).")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    if sys.argv[1] == "--all-missing":
        backfill_all_missing()
        return
    slug = sys.argv[1]
    with open(POSTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    post = next((p for p in data.get("posts", []) if p.get("slug") == slug), None)
    if not post:
        print(f"No post found with slug '{slug}'")
        sys.exit(1)
    url = generate_feature_image(post)
    print(f"wrote {OUT_DIR / (slug + '.png')}" if url else "failed")


if __name__ == "__main__":
    main()
