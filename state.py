"""Seen/unseen state tracking for the Agentic Attention System.

Maintains a small JSON file per session so hook invocations (separate
processes) can share state. Keyed by transcript_path — each Claude Code
session gets its own state file under /tmp/agentic-attention/.

State flow:
  Stop/Notification → write {seen: false, ...} → tab shows 🟡
  UserPromptSubmit  → read state → if unseen, clear marker → mark seen
  SessionStart      → clear state
"""

import hashlib
import json
import os

STATE_DIR = "/tmp/agentic-attention"


def _state_path(transcript_path: str) -> str:
    """Deterministic file path for a session's state."""
    key = hashlib.md5(transcript_path.encode()).hexdigest()[:12]
    return os.path.join(STATE_DIR, f"{key}.json")


def read_state(transcript_path: str) -> dict:
    """Read current session state. Returns empty dict if none."""
    if not transcript_path:
        return {}
    path = _state_path(transcript_path)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def write_state(transcript_path: str, tier: str, project: str, detail: str) -> None:
    """Mark session as unseen with context about what happened."""
    if not transcript_path:
        return
    os.makedirs(STATE_DIR, exist_ok=True)
    state = {
        "seen": False,
        "tier": tier,
        "project": project,
        "detail": detail,
    }
    path = _state_path(transcript_path)
    try:
        with open(path, "w") as f:
            json.dump(state, f)
    except OSError:
        pass


def mark_seen(transcript_path: str) -> dict:
    """Mark session as seen. Returns the previous state (for re-rendering the tab)."""
    if not transcript_path:
        return {}
    path = _state_path(transcript_path)
    try:
        with open(path, "r") as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    if state.get("seen"):
        return state  # already seen, no change needed

    state["seen"] = True
    try:
        with open(path, "w") as f:
            json.dump(state, f)
    except OSError:
        pass
    return state


def clear_state(transcript_path: str) -> None:
    """Remove session state (e.g. on SessionStart)."""
    if not transcript_path:
        return
    path = _state_path(transcript_path)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        pass
