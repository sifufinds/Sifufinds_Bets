"""
Shared, correctly-weighted tweet character counting and trimming — used by
every agent that posts to X (agent_twitter_posts.py, agent_match_post.py,
agent_transfer_post.py, each of which previously carried its own identical
copy of a naive plain-len() implementation).

Verified against Twitter's own published config (twitter-text v3,
https://raw.githubusercontent.com/twitter/twitter-text/master/config/v3.json,
fetched 2026-08-02): maxWeightedTweetLength=280, defaultWeight=200 (i.e.
weight 2 on a scale of 100), transformedURLLength=23, and exactly four
Unicode ranges get the low weight of 1 — everything else, including every
emoji and symbol block, is weight 2:
  0-4351      Basic Latin, Latin-1/Extended, Greek, Cyrillic, Armenian,
              Hebrew, Arabic, Syriac, Thaana, N'Ko
  8192-8205   General Punctuation (en/em dash, ZWJ/ZWNJ, etc.)
  8208-8223   General Punctuation (hyphens, curly quotes)
  8242-8247   Prime symbols

Found 2026-08-02: the previous plain len()-based count treated every
character as weight 1, so an emoji-heavy tweet (flag emoji especially —
each is 2 Unicode codepoints) could read as e.g. "279/280" to this code
while X's own real counter saw it as genuinely over 280 and permanently
disabled the Post button client-side, with zero error surfaced anywhere.
This looked exactly like a UI/timing bug (confirmed via the 2026-08-01
polling fix: text registers fine, the button is polled for a full 10s and
simply never enables) but was actually X correctly rejecting an
over-length tweet the whole time.
"""
import re

TWITTER_URL_LEN = 23
TWEET_MAX = 280

_WEIGHT_1_RANGES = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
# A regional-indicator pair (flag emoji, e.g. 🇳🇬) is one grapheme to
# Twitter's emoji-aware parser — weight 2 for the pair, not 2 each, or a
# flag-heavy template (this codebase's tip templates use several) would
# overcount and trim tweets shorter than necessary.
_REGIONAL_INDICATOR_START, _REGIONAL_INDICATOR_END = 0x1F1E6, 0x1F1FF

_URL_PATTERN = re.compile(r"https?://\S+")


def _weighted_len(segment: str) -> int:
    total = 0
    i, n = 0, len(segment)
    while i < n:
        cp = ord(segment[i])
        if (_REGIONAL_INDICATOR_START <= cp <= _REGIONAL_INDICATOR_END
                and i + 1 < n
                and _REGIONAL_INDICATOR_START <= ord(segment[i + 1]) <= _REGIONAL_INDICATOR_END):
            total += 2
            i += 2
            continue
        total += 1 if any(lo <= cp <= hi for lo, hi in _WEIGHT_1_RANGES) else 2
        i += 1
    return total


def tweet_len(text: str) -> int:
    """Twitter's real weighted character count: URLs always count as 23
    (t.co shortening) regardless of actual length; every other character
    is weighted 1 or 2 per _WEIGHT_1_RANGES above."""
    count, last = 0, 0
    for m in _URL_PATTERN.finditer(text):
        count += _weighted_len(text[last:m.start()])
        count += TWITTER_URL_LEN
        last = m.end()
    count += _weighted_len(text[last:])
    return count


def trim_to_limit(text: str, limit: int = TWEET_MAX) -> str:
    """Truncate the last line(s) of a tweet that exceeds the limit,
    preserving newlines, using the real weighted count above."""
    if tweet_len(text) <= limit:
        return text
    lines = text.split("\n")
    while lines and tweet_len("\n".join(lines)) > limit:
        last = lines[-1]
        if not last:
            lines.pop()
            continue
        words = last.split()
        if len(words) <= 1:
            lines.pop()
        else:
            lines[-1] = " ".join(words[:-1]) + "..."
    return "\n".join(lines)
