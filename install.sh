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
cp "$SCRIPT_DIR/priorities.toml" "$HOOKS_DIR/"

# Patch notify.py to use ~/.claude/sounds/ (installed location)
sed -i '' 's|os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")|os.path.expanduser("~/.claude/sounds")|' "$HOOKS_DIR/notify.py"

# Copy sounds
cp "$SCRIPT_DIR/sounds/"*.wav "$SOUNDS_DIR/"
cp "$SCRIPT_DIR/sounds/generate.py" "$SOUNDS_DIR/"

echo "Files installed to:"
echo "  $HOOKS_DIR/router.py"
echo "  $HOOKS_DIR/classify.py"
echo "  $HOOKS_DIR/notify.py"
echo "  $HOOKS_DIR/priorities.toml"
echo "  $SOUNDS_DIR/*.wav"
echo ""
echo "Now add the hooks to your ~/.claude/settings.json."
echo "If you already have a \"hooks\" key, merge these entries:"
echo ""
cat <<'SETTINGS'
{
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
