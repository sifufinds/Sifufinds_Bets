#!/bin/bash
# ============================================================
# SifuFinds Breaking News Bot — one-command installer + starter
# Run:  bash agents/python/start_newsbot.sh
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AGENT_DIR="$REPO_ROOT/agents/python"
PLIST_SRC="$AGENT_DIR/com.sifufinds.newsbot.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.sifufinds.newsbot.plist"
ENV_FILE="$AGENT_DIR/.env"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   SifuFinds Breaking News Bot — Setup & Start${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── 1. Check GEMINI_API_KEY ───────────────────────────────────────────────────
GEMINI_KEY=""
if [ -f "$ENV_FILE" ]; then
  GEMINI_KEY=$(grep "^GEMINI_API_KEY=" "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
fi

if [ -z "$GEMINI_KEY" ] || [ ${#GEMINI_KEY} -lt 10 ]; then
  echo -e "${RED}✗ GEMINI_API_KEY is missing in agents/python/.env${NC}"
  echo ""
  echo "  Get your free key in 30 seconds:"
  echo -e "  ${YELLOW}1. Go to: https://aistudio.google.com/app/apikey${NC}"
  echo "  2. Sign in with Google"
  echo "  3. Click 'Create API Key'"
  echo "  4. Copy the key"
  echo "  5. Open agents/python/.env and set:"
  echo -e "     ${YELLOW}GEMINI_API_KEY=your_key_here${NC}"
  echo ""
  echo "  Then re-run:  bash agents/python/start_newsbot.sh"
  echo ""
  exit 1
fi
echo -e "${GREEN}✓ GEMINI_API_KEY found (${#GEMINI_KEY} chars)${NC}"

# ── 2. Install Python deps ────────────────────────────────────────────────────
echo ""
echo "Installing Python dependencies..."
cd "$REPO_ROOT" && uv pip install -q -r "$AGENT_DIR/requirements.txt"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# ── 3. Install launchd plist ──────────────────────────────────────────────────
echo ""
echo "Installing macOS scheduler (runs every 15 min automatically)..."

# Unload existing instance if running
if launchctl list | grep -q "com.sifufinds.newsbot" 2>/dev/null; then
  launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

cp "$PLIST_SRC" "$PLIST_DEST"
launchctl load "$PLIST_DEST"
echo -e "${GREEN}✓ Bot scheduled — runs every 15 minutes automatically${NC}"

# ── 4. First run right now ────────────────────────────────────────────────────
echo ""
echo "Running first batch now (this takes ~30 seconds)..."
cd "$AGENT_DIR"
"$REPO_ROOT/.venv/bin/python" agent_sports_blog.py --category football && \
"$REPO_ROOT/.venv/bin/python" agent_sports_blog.py --category sportnews && \
"$REPO_ROOT/.venv/bin/python" agent_sports_blog.py --ticker-only && \
echo -e "${GREEN}✓ First articles published${NC}" || echo -e "${YELLOW}⚠ First run had an error — check newsbot.log${NC}"

# ── 5. Summary ────────────────────────────────────────────────────────────────
TOTAL=$(python3 -c "import json; d=json.load(open('$REPO_ROOT/blog/posts.json')); print(len(d['posts']))" 2>/dev/null || echo "?")
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Breaking News Bot is LIVE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Blog posts total : $TOTAL"
echo "  Schedule         : Every 15 minutes, automatically"
echo "  Sources          : BBC Sport, ESPN, Guardian, Sky Sports, DuckDuckGo News"
echo "  AI writer        : Google Gemini 1.5 Flash (free tier)"
echo "  Log file         : agents/python/newsbot.log"
echo ""
echo "  To stop the bot  : launchctl unload ~/Library/LaunchAgents/com.sifufinds.newsbot.plist"
echo "  To start again   : launchctl load ~/Library/LaunchAgents/com.sifufinds.newsbot.plist"
echo "  To run manually  : bash agents/python/run_news_bot.sh"
echo ""
