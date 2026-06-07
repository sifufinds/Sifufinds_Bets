"""
Newsbot launcher — called by launchd every 15 minutes.
Equivalent to run_news_bot.sh but invoked via the venv python so launchd's
TCC context (Desktop folder access) is satisfied by the venv binary itself.
After generating posts it commits and pushes so the live site always stays current.
"""
import subprocess
import datetime
from pathlib import Path

AGENT_DIR = Path(__file__).parent
REPO_ROOT = AGENT_DIR.parent.parent
VENV = REPO_ROOT / ".venv" / "bin" / "python"
LOG = AGENT_DIR / "newsbot.log"
MAX_LOG_LINES = 500


def _log(msg: str) -> None:
    with LOG.open("a") as f:
        f.write(msg + "\n")


def _run(args: list[str]) -> int:
    result = subprocess.run([str(VENV)] + args, cwd=str(AGENT_DIR))
    return result.returncode


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + list(args), cwd=str(REPO_ROOT),
                          capture_output=True, text=True)


def _deploy(now: datetime.datetime) -> None:
    """Commit and push new blog content to GitHub so it appears on the live site."""
    timestamp = now.strftime("%Y-%m-%d %H:%M") + " UTC"

    # Pull latest remote changes first to avoid conflicts
    _log("[deploy] pulling latest from origin...")
    pull = _git("pull", "--rebase", "origin", "main")
    if pull.returncode != 0:
        _log(f"  [warn] git pull failed: {pull.stderr.strip()}")

    # Stage the blog files that the agent writes
    _git("add",
         "blog/posts.json",
         "blog/posts-data.js",
         "blog/ticker.json",
         "blog/ticker-data.js")

    # Nothing to commit → skip
    diff = _git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        _log("[deploy] no new content to commit — skipping push")
        return

    commit = _git(
        "commit",
        "-m", f"live: breaking news {timestamp}",
        "--author", "SifuFinds Breaking News Bot <newsbot@sifufinds.com>",
    )
    if commit.returncode != 0:
        _log(f"  [warn] git commit failed: {commit.stderr.strip()}")
        return

    # Retry push up to 5 times to handle concurrent push conflicts
    for attempt in range(1, 6):
        push = _git("push", "origin", "main")
        if push.returncode == 0:
            _log(f"[deploy] ✓ pushed on attempt {attempt}")
            return
        if attempt == 5:
            _log(f"[deploy] ✗ push failed after 5 attempts — will retry next run")
            return
        _log(f"  [deploy] push rejected (attempt {attempt}/5) — rebasing...")
        _git("fetch", "origin", "main")
        rebase = _git("rebase", "origin/main")
        if rebase.returncode != 0:
            _git("rebase", "--abort")
            _log("  [deploy] rebase aborted — will retry next run")
            return


def _rotate_log() -> None:
    if LOG.exists():
        lines = LOG.read_text().splitlines()
        if len(lines) > MAX_LOG_LINES:
            LOG.write_text("\n".join(lines[-200:]) + "\n")


WC_START = datetime.datetime(2026, 6, 11)
WC_END   = datetime.datetime(2026, 7, 20)


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

    # Commit and push everything so the live site updates automatically
    _deploy(now)

    _log("Done.")


if __name__ == "__main__":
    main()
