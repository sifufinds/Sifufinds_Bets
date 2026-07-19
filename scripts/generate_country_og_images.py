#!/usr/bin/env python3
"""Generate unique per-post OG/social preview images for country pages.

Same reasoning as generate_review_og_images.py — extends the multi-modal
GEO fix from bookmaker reviews to country pages. Draws each country's real
flag (flags.py — actual official colours/layout, fine emblems omitted per
that module's docstring) rather than relying on emoji-font flag rendering,
since this Pillow build has no raqm/text-shaping support to combine the two
regional-indicator codepoints into one flag glyph. No AI image generation.
South Africa's six-colour Y-shape flag isn't in flags.py (not reducible to
bands/diagonals without misrepresenting it) — that page keeps a typographic
treatment instead of a wrong flag.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from flags import FLAGS, build_flag  # noqa: E402

ROOT = Path(__file__).parent.parent
OUT = ROOT / "assets" / "og"
FONT_DIR = Path("/System/Library/Fonts/Supplemental")

W, H = 1200, 630
GREEN_DARK = (10, 61, 30)
GREEN_LIGHT = (26, 107, 53)
GOLD = (245, 197, 66)
WHITE = (255, 255, 255)

# slug -> display name. "uganda" and "south-africa" have no flags.py entry
# (Uganda's flag centres a grey crane emblem that's meaningless as plain
# bands; South Africa's six-colour Y-shape isn't reducible to bands/diagonals
# at all) — both get the typographic-only treatment rather than a wrong flag.
COUNTRIES = {
    "angola":        "Angola",
    "botswana":      "Botswana",
    "cameroon":      "Cameroon",
    "dr-congo":      "DR Congo",
    "egypt":         "Egypt",
    "ethiopia":      "Ethiopia",
    "ghana":         "Ghana",
    "ivory-coast":   "Ivory Coast",
    "kenya":         "Kenya",
    "liberia":       "Liberia",
    "malawi":        "Malawi",
    "morocco":       "Morocco",
    "mozambique":    "Mozambique",
    "namibia":       "Namibia",
    "nigeria":       "Nigeria",
    "rwanda":        "Rwanda",
    "senegal":       "Senegal",
    "sierra-leone":  "Sierra Leone",
    "south-africa":  "South Africa",
    "tanzania":      "Tanzania",
    "uganda":        "Uganda",
    "zambia":        "Zambia",
    "zimbabwe":      "Zimbabwe",
}


def _gradient_bg() -> Image.Image:
    top = Image.new("RGB", (W, H), GREEN_DARK)
    bottom = Image.new("RGB", (W, H), GREEN_LIGHT)
    mask = Image.new("L", (W, H))
    mask.putdata([int(255 * ((x + y) / (W + H))) for y in range(H) for x in range(W)])
    return Image.composite(bottom, top, mask)


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def build_image(slug: str, display_name: str) -> Image.Image:
    img = _gradient_bg()
    draw = ImageDraw.Draw(img, "RGBA")

    ring_center = (W - 180, 120)
    for r, alpha in [(260, 14), (200, 18), (140, 22)]:
        draw.ellipse(
            [ring_center[0] - r, ring_center[1] - r, ring_center[0] + r, ring_center[1] + r],
            outline=(*GOLD, alpha), width=3,
        )

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

    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=28, fill=WHITE)

    if slug in FLAGS:
        # Real flag, drawn from actual official colours/layout (flags.py) at
        # a standard 3:2 ratio, rounded corners to match the card style.
        flag_w, flag_h = 300, 200
        flag_img = build_flag(slug, flag_w * 3, flag_h * 3).resize((flag_w, flag_h), Image.LANCZOS)
        mask = Image.new("L", (flag_w, flag_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, flag_w, flag_h], radius=14, fill=255)
        border = Image.new("RGBA", (flag_w + 6, flag_h + 6), (0, 0, 0, 0))
        ImageDraw.Draw(border).rounded_rectangle([0, 0, flag_w + 6, flag_h + 6], radius=16, outline=(0, 0, 0, 40), width=2)
        fx = card_x + (card_w - flag_w) // 2
        fy = card_y + (card_h - flag_h) // 2
        img.paste(border, (fx - 3, fy - 3), border)
        img.paste(flag_img, (fx, fy), mask)
    else:
        # No accurate simple-shape rendering exists for this flag (see
        # COUNTRIES comment) — a large gold country-code monogram instead of
        # guessing at the real design.
        code = "".join(w[0] for w in display_name.split())[:2].upper()
        f_mono = _font("Arial Black.ttf", 150)
        bbox = draw.textbbox((0, 0), code, font=f_mono)
        mono_w, mono_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((card_x + (card_w - mono_w) / 2 - bbox[0], card_y + (card_h - mono_h) / 2 - bbox[1]),
                   code, font=f_mono, fill=GREEN_DARK)

    text_x = card_x + card_w + 70
    f_kicker = _font("Arial Bold.ttf", 26)
    f_headline = _font("Arial Black.ttf", 52)
    f_sub = _font("Arial.ttf", 28)

    draw.text((text_x, 168), "SIFUFINDS COUNTRY GUIDE", font=f_kicker, fill=GOLD)
    draw.text((text_x, 205), display_name, font=f_headline, fill=WHITE)
    draw.text((text_x, 275), "Betting Guide 2026", font=f_headline, fill=GOLD)

    y = 380
    for line in ["Licensed Bookmakers  ·  Bonuses", "Payment Methods  ·  Odds"]:
        draw.text((text_x, y), line, font=f_sub, fill=(230, 235, 232))
        y += 40

    f_brand = _font("Arial Bold.ttf", 24)
    draw.text((60, H - 62), "SIFUFINDS", font=f_brand, fill=GOLD)
    draw.text((60, H - 34), "Africa's Betting Comparison Platform", font=_font("Arial.ttf", 18), fill=(200, 210, 205))

    return img.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, display_name in COUNTRIES.items():
        img = build_image(slug, display_name)
        out_path = OUT / f"country-{slug}.png"
        img.save(out_path, "PNG", optimize=True)
        print(f"wrote {out_path} ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
