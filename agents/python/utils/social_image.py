"""
Branded social card generator for Facebook photo posts.

Free by default (Pillow, no API calls, no cost, runs 3x/day forever). An
optional AI-generated image path exists behind SIFU_ALLOW_AI_IMAGES=1 (same
opt-in-gate pattern as SIFU_ALLOW_PAID_CRAWL in utils/serp_research.py) and
always falls back to the free card on any failure, so image generation can
never break a scheduled post.
"""
import hashlib
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 1200, 630  # Meta's recommended Page photo/link-share ratio
OUT_DIR = Path(__file__).parent.parent / "generated_images"

_DEFAULT_COLOR = "#0a5c36"  # SifuFinds green

# Known-brand colours for recognisable, on-brand cards. Anything not listed
# falls back to a deterministic colour derived from the brand name, so every
# bookmaker/post still gets a distinct, stable card instead of one grey default.
BRAND_COLORS = {
    "Bet9ja": "#008751", "Sportybet": "#E60023", "BetKing": "#C1272D",
    "1xBet": "#1565C0", "Betway": "#000000", "Hollywoodbets": "#FCD116",
    "Betika": "#00853F", "SportPesa": "#007A4D", "Melbet": "#1a6b35",
    "MozzartBet": "#B8860B", "NairaBet": "#005CA9", "22Bet": "#F5A623",
    "Betpawa": "#FF6600", "BetWinner": "#2E7D32", "Odibets": "#00AA55",
    "Supabets": "#C1272D", "Bangbet": "#FF4500",
}

_SYSTEM_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in _SYSTEM_FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)  # Pillow >=10.1, always available


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def brand_color(name: str) -> str:
    if name in BRAND_COLORS:
        return BRAND_COLORS[name]
    digest = hashlib.md5(name.encode()).hexdigest()
    r, g, b = int(digest[0:2], 16), int(digest[2:4], 16), int(digest[4:6], 16)
    # Pull toward mid-dark tones so white text always stays readable.
    r, g, b = (r + 20) // 2, (g + 60) // 2, (b + 40) // 2
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_card(
    headline: str,
    tag: str,
    color_hex: str = _DEFAULT_COLOR,
    subtext: str = "",
    out_name: str = "card.png",
) -> Path:
    """Free, deterministic branded card. Never raises — worst case is a plain fallback."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / out_name

    try:
        base = _hex_to_rgb(color_hex)
    except Exception:
        base = _hex_to_rgb(_DEFAULT_COLOR)
    dark = tuple(int(c * 0.35) for c in base)

    img = Image.new("RGB", (CARD_W, CARD_H), base)
    draw = ImageDraw.Draw(img)

    # Vertical gradient background, brand colour → near-black
    for y in range(CARD_H):
        row_color = _lerp(base, dark, y / CARD_H)
        draw.line([(0, y), (CARD_W, y)], fill=row_color)

    # Diagonal accent band (adds depth/layering rather than a flat fill)
    draw.polygon(
        [(CARD_W * 0.62, 0), (CARD_W, 0), (CARD_W, CARD_H), (CARD_W * 0.78, CARD_H)],
        fill=tuple(min(255, c + 30) for c in base),
    )

    # Tag pill (top-left)
    tag_font = _font(30)
    pad_x, pad_y = 22, 12
    tag_w = draw.textlength(tag.upper(), font=tag_font)
    pill_box = (60, 50, 60 + tag_w + pad_x * 2, 50 + 30 + pad_y * 2)
    draw.rounded_rectangle(pill_box, radius=24, fill=(255, 255, 255))
    draw.text((pill_box[0] + pad_x, pill_box[1] + pad_y - 2), tag.upper(), font=tag_font, fill=base)

    # Headline (word-wrapped, drop shadow for legibility over the gradient)
    headline_font = _font(64)
    lines = _wrap(headline, headline_font, CARD_W - 140, draw)[:4]
    line_height = 76
    total_h = len(lines) * line_height
    start_y = (CARD_H - total_h) // 2 - 20
    for i, line in enumerate(lines):
        y = start_y + i * line_height
        draw.text((72, y + 2), line, font=headline_font, fill=(0, 0, 0))
        draw.text((70, y), line, font=headline_font, fill=(255, 255, 255))

    if subtext:
        sub_font = _font(34)
        draw.text((72, start_y + total_h + 18), subtext, font=sub_font, fill=(235, 235, 235))

    # Brand wordmark (bottom-left)
    brand_font = _font(38)
    draw.text((72, CARD_H - 90), "SIFUFINDS.COM", font=brand_font, fill=(255, 255, 255))
    draw.text((72, CARD_H - 52), "Africa's Betting Comparison Site", font=_font(24), fill=(220, 220, 220))

    img.save(out_path, "PNG")
    return out_path


def generate_ai_card(prompt: str, out_name: str = "card_ai.png") -> Path | None:
    """
    Optional richer image via Gemini image generation. Opt-in only
    (SIFU_ALLOW_AI_IMAGES=1 + GEMINI_API_KEY) so scheduled posts never burn
    API credits unless a human deliberately flips the flag. Returns None on
    any failure so callers fall back to generate_card().
    """
    if os.getenv("SIFU_ALLOW_AI_IMAGES", "") != "1":
        return None
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
        )
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) is not None:
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                out_path = OUT_DIR / out_name
                out_path.write_bytes(part.inline_data.data)
                return out_path
    except Exception as e:
        print(f"⚠ AI image generation skipped: {e}")
    return None


def build_social_image(
    headline: str,
    tag: str,
    color_hex: str = _DEFAULT_COLOR,
    subtext: str = "",
    out_name: str = "card.png",
    ai_prompt: str | None = None,
) -> Path:
    """Try the opt-in AI path first (if enabled), else the free branded card."""
    if ai_prompt:
        ai_path = generate_ai_card(ai_prompt, out_name=out_name.replace(".png", "_ai.png"))
        if ai_path:
            return ai_path
    return generate_card(headline, tag, color_hex=color_hex, subtext=subtext, out_name=out_name)
