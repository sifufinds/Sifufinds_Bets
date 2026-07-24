#!/usr/bin/env python3
"""Generate a unique per-post feature image for any blog post.

Every blog post previously shared one identical sitewide og-image.png (or a
generic stock category photo on the blog listing page) — the same gap the
2026-07-19 GEO audit flagged for bookmaker reviews (see
generate_review_og_images.py). This script closes that gap for the general
content pipeline (agent_sports_blog.py, gen_blog_post_pages.py NEW_POSTS)
so every post gets its own on-brand 1200x630 image driven entirely by data
already on the post (image_color, image_icon, category, title) — no stock
photos, no AI image generation, no fabricated branding.

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

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent
POSTS_JSON = ROOT / "blog" / "posts.json"
OUT_DIR = ROOT / "assets" / "og"

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


def generate_feature_image(post: dict) -> str | None:
    """Generate assets/og/{slug}.png for one post. Returns the site-relative
    URL on success, None on failure (never raises — a broken image must not
    block publishing the post itself)."""
    slug = post.get("slug")
    if not slug:
        return None
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
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
