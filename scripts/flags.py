"""Real national flag rendering (bands/diagonals/stars only — fine emblems
like Kenya's shield or Ethiopia's sun are omitted, a standard simplification
used by most web flag-icon sets). Drawn from each country's actual official
colours and layout, not fabricated or AI-generated. South Africa's six-colour
Y-shape is excluded (see build_flag()'s caller) rather than rendered wrong.

Each entry: kind + params.
  ("h", [(color, weight), ...])                    horizontal bands, top→bottom
  ("v", [(color, weight), ...])                     vertical bands, left→right
  ("diag", bg1, bg2, band_color, edge_color)        diagonal split (NW bg1 / SE bg2)
                                                     with a diagonal band + thin edging
  extras: list of ("star", color, cx_frac, cy_frac, size_frac) /
          ("canton", color, w_frac, h_frac) / ("canton_star", star_color)
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

FLAGS = {
    "nigeria":      ("v", [("#008751", 1), ("#FFFFFF", 1), ("#008751", 1)], []),
    "ivory-coast":  ("v", [("#F77F00", 1), ("#FFFFFF", 1), ("#009E60", 1)], []),
    "cameroon":     ("v", [("#007A5E", 1), ("#CE1126", 1), ("#FCD116", 1)],
                     [("star", "#FCD116", 0.5, 0.5, 0.16)]),
    "senegal":      ("v", [("#00853F", 1), ("#FDEF42", 1), ("#E31B23", 1)],
                     [("star", "#00853F", 0.5, 0.5, 0.16)]),
    "ghana":        ("h", [("#CE1126", 1), ("#FCD116", 1), ("#006B3F", 1)],
                     [("star", "#000000", 0.5, 0.5, 0.14)]),
    "sierra-leone": ("h", [("#1EB53A", 1), ("#FFFFFF", 1), ("#0072C6", 1)], []),
    "egypt":        ("h", [("#CE1126", 1), ("#FFFFFF", 1), ("#000000", 1)], []),
    "morocco":      ("h", [("#C1272D", 1)], [("pentagram", "#006233", 0.5, 0.5, 0.22)]),
    "ethiopia":     ("h", [("#078930", 1), ("#FCDD09", 1), ("#DA121A", 1)], []),
    "kenya":        ("h", [("#000000", 3), ("#FFFFFF", 1), ("#BB0000", 3), ("#FFFFFF", 1), ("#006600", 3)], []),
    "malawi":       ("h", [("#000000", 1), ("#CE1126", 1), ("#00A651", 1)], []),
    "rwanda":       ("h", [("#00A1DE", 6), ("#FCD116", 1), ("#00A651", 3)], []),
    "zimbabwe":     ("h", [("#006400", 1), ("#FCE300", 1), ("#DE2010", 1), ("#000000", 1), ("#DE2010", 1), ("#FCE300", 1), ("#006400", 1)],
                     [("hoist_triangle", "#FFFFFF"), ("hoist_star", "#DE2010")]),
    "mozambique":   ("h", [("#009739", 1), ("#FFFFFF", 0), ("#000000", 1), ("#FFFFFF", 0), ("#FFCE00", 1)],
                     [("hoist_triangle", "#DE2010")]),
    "angola":       ("h", [("#CE1126", 1), ("#000000", 1)], []),
    "botswana":     ("h", [("#75AADB", 5), ("#FFFFFF", 1), ("#000000", 2), ("#FFFFFF", 1), ("#75AADB", 5)], []),
    "liberia":      ("h", [("#BF0A30", 1), ("#FFFFFF", 1)] * 5 + [("#BF0A30", 1)],
                     [("canton", "#002868", 0.5, 6 / 11), ("canton_star", "#FFFFFF")]),
    "zambia":       ("solid", "#198A00", [("bar", "#DE2010", 0.60), ("bar", "#000000", 0.70), ("bar", "#FF7900", 0.80)]),
    "namibia":      ("diag", "#003580", "#009543", "#D21034", "#FFFFFF"),
    "tanzania":     ("diag", "#1EB53A", "#00A3DD", "#000000", "#FCD116"),
    "dr-congo":     ("diagband", "#007FFF", "#CE1021", "#F7D618"),
}


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _star_points(cx: float, cy: float, r_outer: float, r_inner: float, points: int = 5, rotation: float = -90) -> list[tuple[float, float]]:
    pts = []
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        angle = math.radians(rotation + i * 360 / (points * 2))
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def _draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str, outline_only: bool = False):
    pts = _star_points(cx, cy, size, size * 0.382)
    if outline_only:
        draw.polygon(pts, outline=_hex(color), width=max(2, int(size * 0.06)))
    else:
        draw.polygon(pts, fill=_hex(color))


def build_flag(slug: str, w: int, h: int) -> Image.Image | None:
    spec = FLAGS.get(slug)
    if not spec:
        return None
    img = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    kind = spec[0]

    if kind == "h":
        bands = spec[1]
        total_weight = sum(wt for _, wt in bands)
        y = 0.0
        for color, weight in bands:
            band_h = h * weight / total_weight
            draw.rectangle([0, y, w, y + band_h + 1], fill=_hex(color))
            y += band_h
        for extra in spec[2]:
            _apply_extra(draw, extra, w, h)

    elif kind == "v":
        bands = spec[1]
        total_weight = sum(wt for _, wt in bands)
        x = 0.0
        for color, weight in bands:
            band_w = w * weight / total_weight
            draw.rectangle([x, 0, x + band_w + 1, h], fill=_hex(color))
            x += band_w
        for extra in spec[2]:
            _apply_extra(draw, extra, w, h)

    elif kind == "solid":
        bg, bars = spec[1], spec[2]
        draw.rectangle([0, 0, w, h], fill=_hex(bg))
        bar_w = w * 0.06
        for _, color, x_frac in bars:
            x = w * x_frac
            draw.rectangle([x, 0, x + bar_w, h], fill=_hex(color))

    elif kind == "diag":
        bg1, bg2, band_color, edge_color = spec[1], spec[2], spec[3], spec[4]
        draw.polygon([(0, 0), (w, 0), (0, h)], fill=_hex(bg1))
        draw.polygon([(w, 0), (w, h), (0, h)], fill=_hex(bg2))
        band_half = h * 0.09
        edge_half = band_half + h * 0.035
        draw.line([(0, 0), (w, h)], fill=_hex(edge_color), width=int(edge_half * 2))
        draw.line([(0, 0), (w, h)], fill=_hex(band_color), width=int(band_half * 2))

    elif kind == "diagband":
        bg, band_color, star_color = spec[1], spec[2], spec[3]
        draw.rectangle([0, 0, w, h], fill=_hex(bg))
        band_half = h * 0.11
        fringe_half = band_half + h * 0.045
        draw.line([(0, h), (w, 0)], fill=_hex(star_color), width=int(fringe_half * 2))
        draw.line([(0, h), (w, 0)], fill=_hex(band_color), width=int(band_half * 2))
        _draw_star(draw, w * 0.16, h * 0.16, min(w, h) * 0.1, star_color)

    return img


def _apply_extra(draw: ImageDraw.ImageDraw, extra: tuple, w: int, h: int):
    kind = extra[0]
    if kind == "star":
        _, color, cxf, cyf, sizef = extra
        _draw_star(draw, w * cxf, h * cyf, min(w, h) * sizef, color)
    elif kind == "pentagram":
        _, color, cxf, cyf, sizef = extra
        _draw_star(draw, w * cxf, h * cyf, min(w, h) * sizef, color, outline_only=True)
    elif kind == "hoist_triangle":
        _, color = extra
        draw.polygon([(0, 0), (w * 0.35, h / 2), (0, h)], fill=_hex(color))
    elif kind == "hoist_star":
        _, color = extra
        _draw_star(draw, w * 0.13, h / 2, min(w, h) * 0.09, color)
    elif kind == "canton":
        _, color, wf, hf = extra
        draw.rectangle([0, 0, w * wf, h * hf], fill=_hex(color))
    elif kind == "canton_star":
        _, color = extra
        _draw_star(draw, w * 0.25, h * 0.27, min(w, h) * 0.11, color)
