"""Classification engine for the Agentic Attention System.

Reads a Claude Code session transcript (JSONL), matches the last assistant
message against priority patterns, and detects the active project from
file paths referenced during the session.
"""

import json
import os
import re

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # fallback for <3.11

CONFIG_PATH = os.path.expanduser("~/.claude/hooks/priorities.toml")

# Tier names in priority order (first match wins)
TIER_ORDER = ["critical", "complete", "update"]


def load_config() -> dict:
    """Load and parse priorities.toml."""
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def extract_last_assistant_text(transcript_path: str) -> str:
    """Read the last assistant message text from a JSONL transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""

    lines = []
    try:
        with open(transcript_path, "r") as f:
            lines = f.readlines()
    except (IOError, OSError):
        return ""

    # Walk backwards to find last assistant message
    for line in reversed(lines[-100:]):
        try:
            entry = json.loads(line.strip())
        except (json.JSONDecodeError, ValueError):
            continue

        if entry.get("type") != "assistant":
            continue

        message = entry.get("message", {})
        if message.get("role") != "assistant":
            continue

        # Extract all text blocks, skip tool_use and thinking
        texts = []
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))

        if texts:
            return "\n".join(texts)

    return ""


def classify_priority(text: str, config: dict) -> str:
    """Walk tiers in order, return the first matching tier name."""
    if not text:
        return "update"

    for tier in TIER_ORDER:
        tier_config = config.get(tier, {})
        patterns = tier_config.get("patterns", [])
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    return tier
            except re.error:
                continue  # skip bad regex patterns

    return "update"


def extract_context(text: str, max_len: int = 100) -> str:
    """Pull the most meaningful snippet from the assistant text.

    Prefers questions (lines ending with ?), then lines with file paths,
    then falls back to the last non-empty line.
    """
    if not text:
        return ""

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return ""

    # Prefer lines that are questions
    for line in lines:
        if line.rstrip().endswith("?"):
            return line[:max_len]

    # Then prefer lines mentioning files/paths
    for line in lines:
        words = line.split()
        if "/" in line or (words and "." in words[-1]):
            return line[:max_len]

    # Fall back to last non-empty line
    return lines[-1][:max_len]


def detect_project(transcript_path: str, config: dict) -> str:
    """Identify the active project by scanning file paths in the transcript.

    Applies config["project"]["path_pattern"] as a regex across raw
    transcript lines. The first capture group is treated as the project
    name. Returns the most-referenced project, or empty string if none.

    This works because tool_use blocks (Read, Edit, Write, Grep, etc.)
    embed full file paths in the JSONL — no special parsing needed.
    """
    project_config = config.get("project", {})
    pattern = project_config.get("path_pattern", "")

    if not pattern or not transcript_path or not os.path.exists(transcript_path):
        return ""

    counts: dict[str, int] = {}
    try:
        with open(transcript_path, "r") as f:
            for line in f:
                for match in re.finditer(pattern, line):
                    name = match.group(1)
                    counts[name] = counts.get(name, 0) + 1
    except (IOError, OSError):
        return ""

    return max(counts, key=counts.get) if counts else ""
