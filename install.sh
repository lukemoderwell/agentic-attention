#!/bin/bash
# Install the Agentic Attention System for Claude Code.
#
# Copies hook scripts and sounds into ~/.claude/, then prints
# the JSON block to add to your ~/.claude/settings.json.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$HOME/.claude/hooks"
SOUNDS_DIR="$HOME/.claude/sounds"

echo "Installing Agentic Attention System..."
echo ""

# Create directories
mkdir -p "$HOOKS_DIR" "$SOUNDS_DIR"

# Copy hook scripts
cp "$SCRIPT_DIR/router.py"       "$HOOKS_DIR/"
cp "$SCRIPT_DIR/classify.py"     "$HOOKS_DIR/"
cp "$SCRIPT_DIR/notify.py"       "$HOOKS_DIR/"

# Copy config only if it doesn't exist (don't overwrite customizations)
if [ ! -f "$HOOKS_DIR/priorities.toml" ]; then
    cp "$SCRIPT_DIR/priorities.toml" "$HOOKS_DIR/"
else
    echo "  priorities.toml already exists — skipping (won't overwrite your config)"
fi

# Copy statusline
cp "$SCRIPT_DIR/statusline.sh" "$HOME/.claude/statusline.sh"
chmod +x "$HOME/.claude/statusline.sh"

# Copy sounds
cp "$SCRIPT_DIR/sounds/"*.wav "$SOUNDS_DIR/"
cp "$SCRIPT_DIR/sounds/generate.py" "$SOUNDS_DIR/"

echo "Files installed to:"
echo "  $HOOKS_DIR/router.py"
echo "  $HOOKS_DIR/classify.py"
echo "  $HOOKS_DIR/notify.py"
echo "  $HOOKS_DIR/priorities.toml"
echo "  $HOME/.claude/statusline.sh"
echo "  $SOUNDS_DIR/*.wav"
echo ""
echo "Now add the hooks to your ~/.claude/settings.json."
echo "If you already have a \"hooks\" key, merge these entries:"
echo ""
cat <<'SETTINGS'
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2
  },
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/router.py",
            "timeout": 10
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/router.py",
            "timeout": 10
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/router.py",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/router.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
SETTINGS
echo ""
echo "Then edit ~/.claude/hooks/priorities.toml to set your path_pattern."
echo "Done."
