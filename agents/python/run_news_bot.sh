#!/bin/bash
# SifuFinds Breaking News Bot — called by macOS launchd every 15 minutes.
# Fetches live RSS/DuckDuckGo headlines, writes AI articles, syncs blog files.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="$REPO_ROOT/.venv/bin/python"
AGENT_DIR="$REPO_ROOT/agents/python"
LOG="$REPO_ROOT/agents/python/newsbot.log"
MAX_LOG_LINES=500

cd "$AGENT_DIR"

echo "" >> "$LOG"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"

# Rotate log if too large
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt "$MAX_LOG_LINES" ]; then
  tail -n 200 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

# Football always (biggest audience)
"$VENV" agent_sports_blog.py --category football >> "$LOG" 2>&1 || true

# Rotating secondary category based on 15-min slot
SLOT=$(( ($(date +%H) * 4 + $(date +%M) / 15) % 8 ))
case $SLOT in
  0) CAT="sportnews"  ;;
  1) CAT="basketball" ;;
  2) CAT="tennis"     ;;
  3) CAT="cricket"    ;;
  4) CAT="rugby"      ;;
  5) CAT="boxing"     ;;
  6) CAT="f1"         ;;
  7) CAT="igaming"    ;;
esac

"$VENV" agent_sports_blog.py --category "$CAT" >> "$LOG" 2>&1 || true

# Always refresh ticker
"$VENV" agent_sports_blog.py --ticker-only >> "$LOG" 2>&1 || true

echo "Done." >> "$LOG"
