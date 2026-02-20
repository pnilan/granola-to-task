# granola-to-task

Extract action items from recent [Granola](https://www.granola.ai/) meeting notes using AI.

A CLI tool that fetches your recent meeting notes via the [Airbyte Agent Granola connector](https://github.com/airbytehq/airbyte-agent-connectors/tree/main/connectors/granola), analyzes each note with Claude, and returns a structured list of action items with assignees and deadlines.

## How it works

1. Connects to Granola via Airbyte's hosted agent connector
2. Searches for meeting notes created within the specified time window
3. Fetches full note content (summary + transcript) for each result
4. Uses a PydanticAI agent (Claude Sonnet) to extract action items from each note
5. Outputs results as formatted text or JSON

## Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- An [Anthropic API key](https://console.anthropic.com/)
- Airbyte Cloud credentials (client ID + secret) with a provisioned Granola connector

### Install

```bash
git clone https://github.com/pnilan/granola-to-task.git
cd granola-to-task
uv sync
```

### Configure

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=your-anthropic-api-key
AIRBYTE_CLIENT_ID=your-airbyte-client-id
AIRBYTE_CLIENT_SECRET=your-airbyte-client-secret
AIRBYTE_CUSTOMER_NAME=your-customer-name
```

## Usage

```bash
# Extract action items from the last 7 days (default)
uv run granola-to-task

# Look back 14 days
uv run granola-to-task --days 14

# Output as JSON
uv run granola-to-task --format json

# Enable verbose logging (connector actions)
uv run granola-to-task -v

# Enable debug logging (includes HTTP requests)
uv run granola-to-task --debug
```

### Example output

```
## Weekly Sync (2026-02-18)
  1. Update the onboarding docs with new API endpoints [@Alex] (due: 2026-02-20)
  2. Schedule follow-up with design team [@Jordan]
  3. Review and merge open PRs before release [@Sam] (due: 2026-02-21)
```

## Project structure

```
src/granola_to_task/
├── main.py      # CLI entry point and argument parsing
├── source.py    # Granola connector setup and note fetching
├── agent.py     # PydanticAI agent for action item extraction
└── models.py    # Pydantic models (ActionItem, MeetingActionItems)
```
