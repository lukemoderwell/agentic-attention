"""Smart notification router for the Agentic Attention System.

Reads hook event JSON from stdin, identifies the active project,
classifies priority, and dispatches to sound + tab-title notifications.

Single entry point for all Claude Code hook events:
  SessionStart, UserPromptSubmit, Stop, Notification.

Configure behavior in priorities.toml (same directory).
"""

import json
import sys
import os

# Add this directory to path so imports work when invoked from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from classify import (
    load_config,
    extract_last_assistant_text,
    classify_priority,
    extract_context,
    detect_project,
)
from notify import set_tab_title, play_sound


# ── Project resolution ──────────────────────────────────────────────


def cwd_label(event: dict) -> str:
    """Short label from the working directory."""
    cwd = event.get("cwd", "")
    if not cwd:
        return "claude"
    return os.path.basename(cwd.rstrip("/")) or "claude"


def resolve_project(event: dict, config: dict) -> str:
    """Best-effort project name: transcript file paths → fallback → cwd."""
    detected = detect_project(event.get("transcript_path", ""), config)
    if detected:
        return detected
    return config.get("project", {}).get("fallback", "") or cwd_label(event)


# ── Tab title ────────────────────────────────────────────────────────


def tab(project: str, symbol: str, detail: str) -> None:
    """Set terminal tab title as 'project symbol detail'."""
    set_tab_title(f"{project} {symbol} {detail}")


# ── Hook handlers ────────────────────────────────────────────────────


def handle_session_start(event: dict, config: dict) -> None:
    states = config.get("states", {})
    tab(cwd_label(event), states.get("starting", "↻"), "starting")


def handle_user_prompt(event: dict, config: dict) -> None:
    project = resolve_project(event, config)
    states = config.get("states", {})
    tab(project, states.get("working", "↻"), "working")


def handle_stop(event: dict, config: dict) -> None:
    """Classify the last assistant message and route notification."""
    project = resolve_project(event, config)
    transcript_path = event.get("transcript_path", "")
    text = extract_last_assistant_text(transcript_path)

    tier = classify_priority(text, config)
    tier_config = config.get(tier, {})
    symbol = tier_config.get("symbol", "·")
    context = extract_context(text)

    if tier == "critical":
        detail = context[:40] if context else "needs input"
    elif tier == "complete":
        detail = "done"
    else:
        detail = "idle"

    play_sound(tier_config.get("sound", ""))
    tab(project, symbol, detail)


def handle_notification(event: dict, config: dict) -> None:
    """Route system notifications — permission/idle are always critical."""
    project = resolve_project(event, config)
    notification_type = event.get("notification_type", "")
    states = config.get("states", {})

    if notification_type == "permission_prompt":
        play_sound(config.get("critical", {}).get("sound", "error.wav"))
        tab(project, states.get("permission", "⏸"), "approve?")
        return

    if notification_type == "idle_prompt":
        play_sound(config.get("critical", {}).get("sound", "error.wav"))
        tab(project, states.get("waiting", "⏳"), "waiting")
        return

    # All other notifications — silent, keep working state
    tab(project, states.get("working", "↻"), "working")


HANDLERS = {
    "SessionStart": handle_session_start,
    "UserPromptSubmit": handle_user_prompt,
    "Stop": handle_stop,
    "Notification": handle_notification,
}


# ── Entry point ──────────────────────────────────────────────────────


def main() -> None:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return

    config = load_config()
    hook_event = event.get("hook_event_name", "")
    handler = HANDLERS.get(hook_event)
    if handler:
        handler(event, config)


if __name__ == "__main__":
    main()
