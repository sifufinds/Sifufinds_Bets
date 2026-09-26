"""Tests for the RapidWombat webhook importer.
Run: python3 agents/python/test_rapidwombat_import.py (also collected by pytest if installed)."""
from __future__ import annotations

import base64
import gzip
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_rapidwombat_import as rw  # noqa: E402

BODY = "# Best Betting Sites in Kenya\n\n" + ("Kenyan punters compare SportyBet and Betway odds weekly. " * 60)


def _payload(**overrides) -> dict:
    return {"id": "abc123", "title": "Best Betting Sites in Kenya", "content": BODY,
            "cover_image": "", **overrides}


def _raises_rejected(fn) -> bool:
    try:
        fn()
    except rw.ArticleRejected:
        return True
    return False


def test_decodes_gzip_content_from_php_forwarder():
    packed = base64.b64encode(gzip.compress(BODY.encode())).decode()
    article = rw.decode_payload(_payload(content=None, content_gzip_b64=packed))
    assert article["content"] == BODY.strip()


def test_rejects_thin_or_malformed_articles():
    assert _raises_rejected(lambda: rw.decode_payload(_payload(content="too short")))
    assert _raises_rejected(lambda: rw.decode_payload(_payload(id="../etc")))
    assert _raises_rejected(lambda: rw.decode_payload(_payload(title="  ")))
    assert _raises_rejected(lambda: rw.decode_payload(_payload(content_gzip_b64="!!", content=None)))


def test_non_http_cover_image_dropped():
    assert rw.decode_payload(_payload(cover_image="javascript:alert(1)"))["cover_image"] == ""


def test_sanitize_strips_leading_h1_and_raw_html():
    out = rw.sanitize_markdown("# Title\n\nHi <script>alert(1)</script> there")
    assert not out.startswith("#")
    assert "<script>" not in out and "&lt;script&gt;" in out


def test_sanitize_neutralises_unsafe_links_keeps_safe_ones():
    out = rw.sanitize_markdown(
        "[bad](javascript:alert(1)) [inject](https://x.com\" onclick=\"y) "
        "[ok](https://www.fifa.com/) ![img](https://cdn.example.com/a.png)"
    )
    assert "javascript:" not in out and "onclick" not in out
    assert "[ok](https://www.fifa.com/)" in out
    assert "![img](https://cdn.example.com/a.png)" in out


def test_slug_is_unique_and_bounded():
    assert rw.unique_slug("kenya-tips", {"kenya-tips", "kenya-tips-2"}) == "kenya-tips-3"
    assert len(rw.slugify("word " * 60)) <= rw.MAX_SLUG_CHARS
    assert rw.slugify("Bet £10, Get €30!") == "bet-10-get-30"


def test_build_post_detects_category_tags_bookmaker():
    article = rw.decode_payload(_payload(title="Top Casino Slots in Nigeria"))
    post = rw.build_post(article, None, set())
    assert post["id"] == "rapidwombat-abc123"
    assert post["category"] == "igaming"
    assert post["tags"] == ["Nigeria"]
    assert post["bookmaker_featured"] == "SportyBet"
    assert 50 <= len(post["excerpt"]) <= 155


def test_update_keeps_slug_and_publish_date():
    existing = {"slug": "original-slug", "published_at": "2026-01-01T00:00:00+00:00"}
    post = rw.build_post(rw.decode_payload(_payload(title="Renamed Title")), existing, set())
    assert post["slug"] == "original-slug"
    assert post["published_at"] == "2026-01-01T00:00:00+00:00"


def test_import_is_idempotent_on_redelivery():
    store: dict = {"posts": [{"id": "post-1", "slug": "best-betting-sites-in-kenya"}]}
    sys.modules["agent_sports_blog"] = types.SimpleNamespace(
        load_posts=lambda: [dict(p) for p in store["posts"]],
        save_posts=lambda posts: store.update(posts=posts),
    )
    sys.modules["generate_blog_feature_image"] = types.SimpleNamespace(
        ensure_feature_image=lambda post: f"/assets/og/{post['slug']}.png",
    )
    sys.modules["utils.title_content_match"] = types.SimpleNamespace(check_africa_framing=lambda *a: None)

    first = rw.import_article(_payload())
    rw.import_article(_payload(title="Best Betting Sites in Kenya (Updated)"))

    imported = [p for p in store["posts"] if p["id"] == "rapidwombat-abc123"]
    assert len(imported) == 1 and len(store["posts"]) == 2
    assert first["slug"] == "best-betting-sites-in-kenya-2"  # existing slug not shadowed
    assert imported[0]["slug"] == first["slug"]
    assert imported[0]["title"].endswith("(Updated)")


if __name__ == "__main__":
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print(f"  ok  {name}")
    print(f"{len(tests)} passed")
