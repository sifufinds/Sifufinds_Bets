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


def main() -> None:
    _rotate_log()
    _log(f"\n=== {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    # Football always (biggest audience)
    _log("[newsbot] running football...")
    _run(["agent_sports_blog.py", "--category", "football"])

    # Rotating secondary category based on 15-min slot (8 slots, one per category)
    now = datetime.datetime.now()
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
