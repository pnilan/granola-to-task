# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

CLI tool that extracts action items from Granola meeting notes using Claude AI. It fetches recent meeting notes via the Granola connector, runs each through a PydanticAI agent, and outputs structured action items.

## Commands

```bash
uv sync                              # Install dependencies
uv run granola-to-task               # Run (default: last 7 days, text output)
uv run granola-to-task --days 14     # Custom lookback window
uv run granola-to-task -v            # Verbose (INFO logging)
uv run granola-to-task --debug       # Debug (DEBUG logging + HTTP traces)
uv run pytest                        # Run tests
uv run ruff check                    # Lint
uv run ruff format                   # Format
```

## Architecture

**Entry point**: `src/granola_to_task/main.py` → `main()` → async `run()`

The pipeline is: **fetch notes → analyze each with AI → output results**.

- **source.py** – Auto-detects execution mode from env vars. Hosted mode uses `AirbyteAuthConfig` (Airbyte Cloud); local mode uses `GranolaAuthConfig` (direct API). Fetches recent notes via search+list (hosted) or list-only (local).
- **agent.py** – PydanticAI agent using `claude-sonnet-4-6`. Formats notes into text prompts and extracts structured `MeetingActionItems` output.
- **models.py** – Pydantic models: `ActionItem` (description, assignee, due_date, source_meeting) and `MeetingActionItems` container.
- **main.py** – CLI via argparse. Orchestrates the pipeline, handles text output formatting, configures logging levels.

## Environment Variables

Required in `.env` (see `.env.example`):
- `ANTHROPIC_API_KEY` – For the PydanticAI agent

**Hosted mode** (preferred, via Airbyte Cloud):
- `AIRBYTE_CLIENT_ID`, `AIRBYTE_CLIENT_SECRET` – Airbyte Cloud credentials
- `AIRBYTE_CUSTOMER_NAME` – Customer name for connector lookup

**Local mode** (direct Granola API calls):
- `GRANOLA_API_KEY` – Granola Enterprise API key

Mode is auto-detected: if `AIRBYTE_*` vars are set, hosted mode is used; otherwise `GRANOLA_API_KEY` is required for local mode.

## Git

- Never add a Co-Authored-By line for Claude in commit messages.

## Key Conventions

- Python 3.14+, managed with `uv`
- All I/O is async (`asyncio`)
- Type hints with `from __future__ import annotations`
- Logging to stderr, results to stdout
