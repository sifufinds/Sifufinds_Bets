"""
utils/gameweek_card.py — composite "gameweek card" image for prediction posts.

Builds one branded PNG listing every fixture in a round with each club's real
crest next to SifuFinds' predicted score, styled after the odds-slip / iGaming
look (gradient header, gold accent band, colour-coded confidence, a pill
around the score) rather than a plain spreadsheet row. Crest images come from
ESPN's own public CDN (the same source agent_predictions.py already uses for
grading), never a placeholder guess — a side whose crest can't be confidently
matched gets a plain lettered circle instead of a wrong or invented badge.
"""
import io
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from utils.social_image import _font, OUT_DIR

CARD_W = 1080
ROW_H = 136
HEADER_H = 190
FOOTER_H = 90
CREST_SIZE = 84

# Deep-green → near-black gradient, matching the site's brand green, with a
# gold accent for headline numbers/dividers — a common odds-slip palette.
_BG_TOP = (10, 58, 38)
_BG_BOTTOM = (5, 18, 12)
_ROW_LINE = (255, 255, 255, 18)
_ACCENT_GOLD = (255, 200, 60)
_CONF_HIGH = (110, 231, 150)     # >=70%
_CONF_MED = (255, 200, 60)       # 60-69%
_CONF_LOW = (170, 178, 176)      # <60%

_crest_cache: dict[str, "Image.Image | None"] = {}


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _confidence_color(conf: int) -> tuple[int, int, int]:
    if conf >= 70:
        return _CONF_HIGH
    if conf >= 60:
        return _CONF_MED
    return _CONF_LOW


def _with_light_backdrop(crest: "Image.Image") -> "Image.Image":
    """Real club crests span every colour, including several (Spurs' navy
    cockerel, for one — confirmed near-invisible in testing) that are far too
    dark to read against this card's dark-green background on their own. A
    light circular backdrop behind every crest keeps them legible regardless
    of the crest's own palette."""
    backdrop = Image.new("RGBA", (CREST_SIZE, CREST_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(backdrop)
    pad = 4
    draw.ellipse((pad, pad, CREST_SIZE - pad, CREST_SIZE - pad), fill=(240, 240, 240, 235))
    return Image.alpha_composite(backdrop, crest)


def _download_crest(url: str | None) -> "Image.Image | None":
    if not url:
        return None
    if url in _crest_cache:
        return _crest_cache[url]
    try:
        resp = requests.get(url, timeout=8)
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        img = img.resize((CREST_SIZE, CREST_SIZE), Image.LANCZOS)
        img = _with_light_backdrop(img)
        _crest_cache[url] = img
        return img
    except Exception:
        _crest_cache[url] = None
        return None


def _placeholder_crest(name: str) -> "Image.Image":
    initial = (name or "?").strip()[:1].upper() or "?"
    img = Image.new("RGBA", (CREST_SIZE, CREST_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, CREST_SIZE - 2, CREST_SIZE - 2), fill=(255, 255, 255, 40), outline=(255, 255, 255, 150), width=3)
    font = _font(34)
    tw = draw.textlength(initial, font=font)
    draw.text(((CREST_SIZE - tw) / 2, CREST_SIZE * 0.2), initial, font=font, fill=(255, 255, 255, 235))
    return img


def _truncate(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    return text + "…"


def _vertical_gradient(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    span = max(y1 - y0, 1)
    for y in range(y0, y1):
        draw.line([(x0, y), (x1, y)], fill=_lerp(top, bottom, (y - y0) / span))


def build_gameweek_card(records: list[dict], title: str, subtitle: str = "", out_name: str = "gameweek_card.png") -> Path:
    n = len(records)
    height = HEADER_H + n * ROW_H + FOOTER_H
    img = Image.new("RGB", (CARD_W, height), _BG_TOP)
    draw = ImageDraw.Draw(img)

    # Full-card vertical gradient sets the base tone; header/footer get a
    # darker overlay band on top so text always has a consistent backdrop.
    _vertical_gradient(draw, (0, 0, CARD_W, height), _BG_TOP, _BG_BOTTOM)
    draw.rectangle([0, 0, CARD_W, HEADER_H], fill=(6, 26, 18))

    # Diagonal gold accent band in the header corner — depth/layering rather
    # than a flat block, same device utils/social_image.py already uses.
    draw.polygon(
        [(CARD_W * 0.72, 0), (CARD_W, 0), (CARD_W, HEADER_H), (CARD_W * 0.86, HEADER_H)],
        fill=(14, 62, 40),
    )

    draw.text((50, 36), title, font=_font(44), fill=(255, 255, 255))
    if subtitle:
        draw.text((50, 96), subtitle, font=_font(28), fill=_ACCENT_GOLD)
    draw.line([(50, HEADER_H - 1), (CARD_W - 50, HEADER_H - 1)], fill=_ACCENT_GOLD, width=3)

    score_font = _font(38)
    name_font = _font(28)
    conf_font = _font(21)

    for i, r in enumerate(records):
        y0 = HEADER_H + i * ROW_H
        if i > 0:
            draw.line([(50, y0), (CARD_W - 50, y0)], fill=_ROW_LINE, width=1)

        home_crest = _download_crest(r.get("home_crest")) or _placeholder_crest(r["home"])
        away_crest = _download_crest(r.get("away_crest")) or _placeholder_crest(r["away"])
        cy = y0 + (ROW_H - CREST_SIZE) // 2
        img.paste(home_crest, (56, cy), home_crest)
        img.paste(away_crest, (CARD_W - 56 - CREST_SIZE, cy), away_crest)

        # Score pill — a rounded, bordered badge (odds-slip styling) rather
        # than bare centred text.
        score_text = r["predicted_score"]
        stw = draw.textlength(score_text, font=score_font)
        pill_w, pill_h = stw + 56, 62
        pill_x0 = (CARD_W - pill_w) / 2
        pill_y0 = y0 + ROW_H / 2 - pill_h / 2 - 12
        draw.rounded_rectangle(
            (pill_x0, pill_y0, pill_x0 + pill_w, pill_y0 + pill_h),
            radius=14, fill=(20, 74, 48), outline=_ACCENT_GOLD, width=2,
        )
        draw.text((pill_x0 + 28, pill_y0 + 10), score_text, font=score_font, fill=(255, 255, 255))

        conf_color = _confidence_color(r["confidence"])
        conf_text = f"{r['confidence']}% CONFIDENCE"
        ctw = draw.textlength(conf_text, font=conf_font)
        draw.text(((CARD_W - ctw) / 2, pill_y0 + pill_h + 8), conf_text, font=conf_font, fill=conf_color)

        home_name = _truncate(r["home"], name_font, 220, draw)
        away_name = _truncate(r["away"], name_font, 220, draw)
        draw.text((56 + CREST_SIZE + 16, y0 + ROW_H / 2 - 16), home_name, font=name_font, fill=(255, 255, 255))
        atw = draw.textlength(away_name, font=name_font)
        draw.text((CARD_W - 56 - CREST_SIZE - 16 - atw, y0 + ROW_H / 2 - 16), away_name, font=name_font, fill=(255, 255, 255))

    footer_y = HEADER_H + n * ROW_H
    draw.rectangle([0, footer_y, CARD_W, height], fill=(6, 26, 18))
    draw.line([(50, footer_y), (CARD_W - 50, footer_y)], fill=_ACCENT_GOLD, width=3)
    # No emoji in footer text — PIL's plain TrueType rendering has no
    # colour-emoji glyphs, so one shows as a tofu box (confirmed live) rather
    # than silently being skipped.
    draw.text((50, footer_y + 28), "SIFUFINDS.COM", font=_font(30), fill=(255, 255, 255))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / out_name
    img.save(out_path, "PNG")
    return out_path
