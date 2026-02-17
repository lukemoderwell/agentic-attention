# Agentic Attention

A priority notification system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that keeps you informed without demanding focus.

When Claude finishes a task, asks a question, or needs approval, you get the right signal — a sound, a tab title update, or both — so you can context-switch away and trust you'll be pulled back at the right moment.

## How it works

Every Claude Code hook event routes through a single Python entry point (`router.py`) that:

1. **Identifies the project** by scanning file paths in the session transcript
2. **Classifies priority** by matching the last assistant message against regex patterns
3. **Dispatches notifications** via sound and terminal tab title

### What you see

| State             | Tab title                          | Sound             |
| ----------------- | ---------------------------------- | ----------------- |
| Session starts    | `my-app ↻ starting`               | —                 |
| You send a prompt | `my-app ↻ working`                | —                 |
| Claude is blocked | `my-app ⚠ should I use Redis?`    | descending tone   |
| Permission needed | `my-app ⏸ approve?`               | descending tone   |
| Waiting for input | `my-app ⏳ waiting`                | descending tone   |
| Task complete     | `my-app ✓ done`                    | ascending melody  |
| Other             | `my-app · idle`                    | —                 |

### Architecture

```
┌─────────────────────────────────────────────────┐
│  Claude Code Hook Events                        │
│  (Stop, Notification, UserPromptSubmit, Start)  │
└────────────────────┬────────────────────────────┘
                     │ JSON via stdin
                     ▼
              ┌─────────────┐
              │  router.py  │  dispatch by event type
              └──────┬──────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
   ┌────────────┐  ┌────┐  ┌────────────────┐
   │ classify.py│  │    │  │ priorities.toml │
   │            │◄─┤    ├─►│                 │
   │ - project  │  │    │  │ - path_pattern  │
   │ - tier     │  │    │  │ - symbols       │
   │ - context  │  │    │  │ - regex tiers   │
   └────────────┘  │    │  └────────────────┘
                   │    │
                   ▼    ▼
              ┌───────────┐
              │ notify.py  │
              │ - afplay   │  sound
              │ - TTY esc  │  tab title
              └───────────┘

┌─────────────────────────────────────────────────┐
│  Claude Code Statusline                         │
│  (JSON via stdin after each response)           │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ statusline.sh  │
            │ - context %    │  fuel gauge
            │ - session cost │  $ display
            │ - model name   │  label
            └────────────────┘
```

## Install

Requires **macOS** and **Python 3.11+** (for `tomllib`; or install `tomli` for older versions).

```bash
git clone https://github.com/lukemoderwell/agentic-attention.git
cd agentic-attention
./install.sh
```

The install script copies files to `~/.claude/hooks/`, `~/.claude/sounds/`, and `~/.claude/statusline.sh`, then prints the JSON to add to your `~/.claude/settings.json`.

### Configure your project pattern

Edit `~/.claude/hooks/priorities.toml` and set `path_pattern` to match your directory structure:

```toml
[project]
# First capture group = project name in the tab
path_pattern = 'packages/([^/]+)/'   # monorepo
# path_pattern = 'clients/([^/]+)/'  # client folders
# path_pattern = 'Work/([^/]+)/'     # Obsidian vault
fallback = "internal"
```

The regex runs against raw file paths in the session transcript. When Claude reads or edits `packages/my-app/src/index.ts`, the tab shows `my-app` instead of a generic label.

## Statusline

A context-aware fuel gauge that sits in the Claude Code status bar alongside built-in git changes.

```
▓▓▓▓▓▓▓░░░ 72% ctx  $0.69  Opus 4.6
```

Shows three things at a glance:

- **Context remaining** — visual bar that drains as the conversation grows, color-coded green → yellow → red
- **Session cost** — equivalent API cost (informational, not billed separately on Pro)
- **Model name** — which model is active

The script reads JSON piped from Claude Code via stdin — no API tokens consumed. It updates after every assistant response.

## Configuration

All hook behavior is controlled by `priorities.toml`:

### Priority tiers

Each tier has a `sound`, `symbol`, and list of regex `patterns`:

```toml
[critical]
sound   = "error.wav"
symbol  = "⚠"
patterns = [
    'should I ',
    'do you (want|prefer|need)',
    'fatal error',
    # ... add your own
]
```

Tiers are checked in order: `critical` → `complete` → `update`. First regex match wins.

### Symbols

The `[states]` section controls symbols for lifecycle events (before classification):

```toml
[states]
starting   = "↻"
working    = "↻"
permission = "⏸"
waiting    = "⏳"
```

### Sounds

Three sounds are included, generated by `sounds/generate.py` (pure Python, no dependencies):

| File                | Character                                    |
| ------------------- | -------------------------------------------- |
| `error.wav`         | Soft descending glide — "something happened" |
| `task_complete.wav` | Ascending bell melody — "finished"           |
| `notification.wav`  | Quick coin-like ping — available for custom use |

Regenerate or tweak them:

```bash
cd sounds && python3 generate.py
```

## Extending

**Add a new tier:** Add a `[mytier]` section to `priorities.toml` with `sound`, `symbol`, and `patterns`. Then add `"mytier"` to the `TIER_ORDER` list in `classify.py`.

**macOS notifications:** The `notify.py` module is the delivery layer. Adding `osascript` or `terminal-notifier` calls there would enable native notification center alerts.

**Linux/Windows:** Replace `afplay` in `notify.py` with `paplay` (PulseAudio) or `powershell -c (New-Object Media.SoundPlayer ...).PlaySync()`. The TTY escape sequences work in most modern terminals.

## How it's built

The system was designed around a core insight: **not all AI stops are equal**. When an agent finishes work, you can take your time. When it's blocked on a decision, every minute of latency is wasted compute. By classifying the *content* of what the AI said — not just the event type — you get priority-aware ambient signals that match the urgency of the moment.

The transcript-reading approach (scanning raw JSONL for file paths and regex patterns) is intentionally simple. No JSON parsing of tool_use blocks, no state machines, no dependencies. It's four files and a config.

## License

MIT
