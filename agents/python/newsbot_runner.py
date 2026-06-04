"""
Newsbot launcher — called by launchd every 15 minutes.
Equivalent to run_news_bot.sh but invoked via the venv python so launchd's
TCC context (Desktop folder access) is satisfied by the venv binary itself.
"""
import subprocess
import sys
import datetime
from pathlib import Path

AGENT_DIR = Path(__file__).parent
VENV = AGENT_DIR.parent.parent / ".venv" / "bin" / "python"
LOG = AGENT_DIR / "newsbot.log"
MAX_LOG_LINES = 500


def _log(msg: str) -> None:
    with LOG.open("a") as f:
        f.write(msg + "\n")


def _run(args: list[str]) -> int:
    result = subprocess.run([str(VENV)] + args, cwd=str(AGENT_DIR))
    return result.returncode


def _rotate_log() -> None:
    if LOG.exists():
        lines = LOG.read_text().splitlines()
        if len(lines) > MAX_LOG_LINES:
            LOG.write_text("\n".join(lines[-200:]) + "\n")


WC_START = datetime.datetime(2026, 6, 11)
WC_END   = datetime.datetime(2026, 7, 20)   # day after final


def _is_wc_active(now: datetime.datetime) -> bool:
    return WC_START <= now <= WC_END


def main() -> None:
    _rotate_log()
    now = datetime.datetime.now()
    _log(f"\n=== {now.strftime('%Y-%m-%d %H:%M:%S')} ===")

    # Football always (biggest audience)
    _log("[newsbot] running football...")
    _run(["agent_sports_blog.py", "--category", "football"])

    # World Cup 2026 — runs on every cycle during the tournament (Jun 11 – Jul 19)
    if _is_wc_active(now):
        _log("[newsbot] running worldcup2026...")
        rc = _run(["agent_sports_blog.py", "--category", "worldcup2026"])
        if rc != 0:
            _log(f"  [warn] worldcup2026 exited {rc}")

    # Rotating secondary category based on 15-min slot (8 slots)
    slot = (now.hour * 4 + now.minute // 15) % 8
    categories = ["sportnews", "basketball", "tennis", "cricket", "rugby", "boxing", "f1", "igaming"]
    cat = categories[slot]

    _log(f"[newsbot] running {cat}...")
    rc = _run(["agent_sports_blog.py", "--category", cat])
    if rc != 0:
        _log(f"  [warn] agent exited {rc}: --category {cat}")

    # Always refresh ticker
    _log("[newsbot] refreshing ticker...")
    _run(["agent_sports_blog.py", "--ticker-only"])

    _log("Done.")


if __name__ == "__main__":
    main()
