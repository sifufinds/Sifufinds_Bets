#!/usr/bin/env python3
"""Generate unique per-post OG/social preview images for bookmaker review posts.

Every one of the 855 blog posts currently shares one identical og-image.png
(the site logo) — flagged in the 2026-07-19 GEO audit as the biggest
remaining gap in the "multi-modal content" category. Real per-post images
raise AI-search selection rates and give each review a distinct, on-brand
social preview instead of the generic sitewide graphic.

Uses only real, already-licensed assets already in assets/logos/ (the same
logos used elsewhere on the site for each bookmaker's own listing) composited
onto a template that reuses the site's own brand gradient (#0a3d1e→#1a6b35,
identical to .post-hero in gen_blog_post_pages.py) — no AI image generation,
no fabricated branding.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent.parent
LOGOS = ROOT / "assets" / "logos"
OUT = ROOT / "assets" / "og"
FONT_DIR = Path("/System/Library/Fonts/Supplemental")

W, H = 1200, 630
GREEN_DARK = (10, 61, 30)
GREEN_LIGHT = (26, 107, 53)
GOLD = (245, 197, 66)
WHITE = (255, 255, 255)

# slug -> (logo filename, display name)
BOOKMAKERS = {
    "1xbet-review":        ("1xbet_hq.png",        "1xBet"),
    "22bet-review":        ("22bet_hq.png",         "22Bet"),
    "bangbet-review":      ("bangbet_hq.png",       "BangBet"),
    "bet9ja-review":       ("bet9ja_hq.png",        "Bet9ja"),
    "betika-review":       ("betika_hq.png",        "Betika"),
    "betking-review":      ("betking_hq.png",       "BetKing"),
    "betpawa-review":      ("betpawa_hq.png",       "betPawa"),
    "betway-review":       ("betway_hq.png",        "Betway"),
    "fairpari-review":     ("fairpari.png",         "FairPari"),
    "hollywoodbets-review": ("hollywoodbets_hq.png", "Hollywoodbets"),
    "melbet-review":       ("melbet_hq.png",        "Melbet"),
    "mozzartbet-review":   ("mozzartbet_hq.png",    "Mozzartbet"),
    "odibets-review":      ("odibets_hq.png",       "Odibets"),
    "sportpesa-review":    ("sportpesa_hq.png",     "SportPesa"),
    "sportybet-review":    ("sportybet.png",        "SportyBet"),
}


def _gradient_bg() -> Image.Image:
    base = Image.new("RGB", (W, H), GREEN_DARK)
    top = Image.new("RGB", (W, H), GREEN_DARK)
    bottom = Image.new("RGB", (W, H), GREEN_LIGHT)
    mask = Image.new("L", (W, H))
    mask_data = [int(255 * ((x + y) / (W + H))) for y in range(H) for x in range(W)]
    mask.putdata(mask_data)
    return Image.composite(bottom, top, mask)


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def build_image(logo_file: str, display_name: str) -> Image.Image:
    img = _gradient_bg()
    draw = ImageDraw.Draw(img, "RGBA")

    # Decorative translucent ring motif (echoes the compass/globe in the site
    # logo) for depth — flat single-gradient panels read as generic template.
    ring_center = (W - 180, 120)
    for r, alpha in [(260, 14), (200, 18), (140, 22)]:
        draw.ellipse(
            [ring_center[0] - r, ring_center[1] - r, ring_center[0] + r, ring_center[1] + r],
            outline=(*GOLD, alpha), width=3,
        )

    # White rounded card holding the bookmaker's own logo
    card_w, card_h = 380, 380
    card_x, card_y = 90, (H - card_h) // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle(
        [card_x + 10, card_y + 14, card_x + card_w + 10, card_y + card_h + 14],
        radius=28, fill=(0, 0, 0, 90),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img.paste(shadow, (0, 0), shadow)

    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=28, fill=WHITE,
    )

    logo = Image.open(LOGOS / logo_file).convert("RGBA")
    pad = 56
    max_dim = card_w - pad * 2
    logo.thumbnail((max_dim, max_dim), Image.LANCZOS)
    lx = card_x + (card_w - logo.width) // 2
    ly = card_y + (card_h - logo.height) // 2
    img.paste(logo, (lx, ly), logo)

    # Headline block
    text_x = card_x + card_w + 70
    text_w = W - text_x - 60

    f_kicker = _font("Arial Bold.ttf", 26)
    f_headline = _font("Arial Black.ttf", 58)
    f_sub = _font("Arial.ttf", 28)

    draw.text((text_x, 168), "SIFUFINDS VERIFIED REVIEW", font=f_kicker, fill=GOLD)

    headline = f"{display_name}"
    draw.text((text_x, 205), headline, font=f_headline, fill=WHITE)
    draw.text((text_x, 285), "Review 2026", font=f_headline, fill=GOLD)

    sub_lines = ["Bonuses  ·  Licence  ·  Odds  ·  Payouts", "for African bettors"]
    y = 380
    for line in sub_lines:
        draw.text((text_x, y), line, font=f_sub, fill=(230, 235, 232))
        y += 40

    # Bottom-left SifuFinds wordmark for brand consistency across all images
    f_brand = _font("Arial Bold.ttf", 24)
    draw.text((60, H - 62), "SIFUFINDS", font=f_brand, fill=GOLD)
    draw.text((60, H - 34), "Africa's Betting Comparison Platform", font=_font("Arial.ttf", 18), fill=(200, 210, 205))

    return img.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    targets = {only: BOOKMAKERS[only]} if only else BOOKMAKERS
    for slug, (logo_file, display_name) in targets.items():
        if not (LOGOS / logo_file).exists():
            print(f"SKIP {slug} — logo not found: {logo_file}")
            continue
        img = build_image(logo_file, display_name)
        out_path = OUT / f"{slug}.png"
        img.save(out_path, "PNG", optimize=True)
        print(f"wrote {out_path} ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
