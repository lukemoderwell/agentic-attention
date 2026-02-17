#!/bin/bash
# Claude Code Statusline — single-line context fuel gauge
# Sits alongside built-in git changes row

input=$(cat)

# --- Extract fields ---
MODEL=$(echo "$input" | jq -r '.model.display_name // "—"')
USED_PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')

# --- Context fuel gauge ---
USED_INT=${USED_PCT%.*}
USED_INT=${USED_INT:-0}
REMAINING=$((100 - USED_INT))

BAR_WIDTH=10
FILLED=$((REMAINING * BAR_WIDTH / 100))
EMPTY=$((BAR_WIDTH - FILLED))

if [ "$REMAINING" -ge 50 ]; then
  COLOR="\033[32m"
elif [ "$REMAINING" -ge 20 ]; then
  COLOR="\033[33m"
else
  COLOR="\033[31m"
fi
RESET="\033[0m"

BAR=$(printf "%${FILLED}s" | tr ' ' '▓')
BAR="${BAR}$(printf "%${EMPTY}s" | tr ' ' '░')"

# --- Cost ---
if [ "$(echo "$COST > 0" | bc 2>/dev/null)" = "1" ]; then
  COST_STR=$(printf "\$%.2f" "$COST")
else
  COST_STR="\$0.00"
fi

# --- Single line output ---
echo -e "${COLOR}${BAR}${RESET} ${REMAINING}% ctx  ${COST_STR}  ${MODEL}"
