"""Notification delivery: sound and tab title.

Part of the Agentic Attention System. Handles two output channels:
  - Sound: plays wav files via macOS afplay (non-blocking)
  - Tab title: writes ANSI escape sequences to the parent TTY
"""

import subprocess
import os


# Default: ~/.claude/sounds/ (standard install location)
# Override with AGENTIC_ATTENTION_SOUNDS env var if needed
SOUNDS_DIR = os.environ.get(
    "AGENTIC_ATTENTION_SOUNDS",
    os.path.expanduser("~/.claude/sounds"),
)


def play_sound(filename: str) -> None:
    """Play a wav file in the background (non-blocking)."""
    if not filename:
        return
    path = os.path.join(SOUNDS_DIR, filename)
    if os.path.exists(path):
        subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _find_parent_tty() -> str:
    """Walk up the process tree to find the first ancestor with a real TTY."""
    pid = os.getpid()
    for _ in range(10):  # max 10 levels up
        try:
            result = subprocess.run(
                ["ps", "-o", "ppid=,tty=", "-p", str(pid)],
                capture_output=True, text=True, timeout=2,
            )
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                ppid, tty = parts[0], parts[1]
                if tty != "??" and tty.startswith("ttys"):
                    return f"/dev/{tty}"
                pid = int(ppid)
            else:
                break
        except (subprocess.TimeoutExpired, ValueError, OSError):
            break
    return ""


# Cache the TTY path for the lifetime of this process
_tty_path: str | None = None


def set_tab_title(title: str) -> None:
    """Set terminal tab title by writing escape sequence to the parent's TTY."""
    global _tty_path
    if _tty_path is None:
        _tty_path = _find_parent_tty()
    if not _tty_path:
        return
    try:
        with open(_tty_path, "w") as tty:
            tty.write(f"\033]0;{title}\007")
            tty.flush()
    except (IOError, OSError):
        pass
