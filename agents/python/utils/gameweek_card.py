"""
utils/gameweek_card.py — composite "gameweek card" image for prediction posts.

Builds one branded PNG listing every fixture in a round with each club's real
crest next to SifuFinds' predicted score. Crest images come from ESPN's own
public CDN (the same source agent_predictions.py already uses for grading),
never a placeholder guess — a side whose crest can't be confidently matched
gets a plain lettered circle instead of a wrong or invented badge.
"""
import io
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from utils.social_image import _font, OUT_DIR

CARD_W = 1080
ROW_H = 130
HEADER_H = 170
FOOTER_H = 90
CREST_SIZE = 84

_BG_DARK = (8, 36, 24)       # SifuFinds dark green
_BG_ROW_ALT = (14, 48, 32)
_ACCENT_GOLD = (255, 200, 60)

_crest_cache: dict[str, "Image.Image | None"] = {}


def _download_crest(url: str | None) -> "Image.Image | None":
    if not url:
        return None
    if url in _crest_cache:
        return _crest_cache[url]
    try:
        resp = requests.get(url, timeout=8)
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        img = img.resize((CREST_SIZE, CREST_SIZE), Image.LANCZOS)
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


def build_gameweek_card(records: list[dict], title: str, subtitle: str = "", out_name: str = "gameweek_card.png") -> Path:
    n = len(records)
    height = HEADER_H + n * ROW_H + FOOTER_H
    img = Image.new("RGB", (CARD_W, height), _BG_DARK)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, CARD_W, HEADER_H], fill=(6, 26, 18))
    draw.text((50, 38), title, font=_font(44), fill=(255, 255, 255))
    if subtitle:
        draw.text((50, 98), subtitle, font=_font(28), fill=_ACCENT_GOLD)

    score_font = _font(36)
    name_font = _font(28)
    conf_font = _font(20)

    for i, r in enumerate(records):
        y0 = HEADER_H + i * ROW_H
        draw.rectangle([0, y0, CARD_W, y0 + ROW_H], fill=(_BG_DARK if i % 2 == 0 else _BG_ROW_ALT))

        home_crest = _download_crest(r.get("home_crest")) or _placeholder_crest(r["home"])
        away_crest = _download_crest(r.get("away_crest")) or _placeholder_crest(r["away"])
        cy = y0 + (ROW_H - CREST_SIZE) // 2
        img.paste(home_crest, (60, cy), home_crest)
        img.paste(away_crest, (CARD_W - 60 - CREST_SIZE, cy), away_crest)

        score_text = r["predicted_score"]
        stw = draw.textlength(score_text, font=score_font)
        draw.text(((CARD_W - stw) / 2, y0 + ROW_H / 2 - 34), score_text, font=score_font, fill=(255, 255, 255))

        conf_text = f"{r['confidence']}% confidence"
        ctw = draw.textlength(conf_text, font=conf_font)
        draw.text(((CARD_W - ctw) / 2, y0 + ROW_H / 2 + 10), conf_text, font=conf_font, fill=(190, 190, 190))

        home_name = _truncate(r["home"], name_font, 230, draw)
        away_name = _truncate(r["away"], name_font, 230, draw)
        draw.text((60 + CREST_SIZE + 16, y0 + ROW_H / 2 - 16), home_name, font=name_font, fill=(255, 255, 255))
        atw = draw.textlength(away_name, font=name_font)
        draw.text((CARD_W - 60 - CREST_SIZE - 16 - atw, y0 + ROW_H / 2 - 16), away_name, font=name_font, fill=(255, 255, 255))

    footer_y = HEADER_H + n * ROW_H
    draw.rectangle([0, footer_y, CARD_W, height], fill=(6, 26, 18))
    draw.text((50, footer_y + 28), "⚽ SIFUFINDS.COM", font=_font(30), fill=(255, 255, 255))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / out_name
    img.save(out_path, "PNG")
    return out_path
