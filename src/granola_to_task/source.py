from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from airbyte_agent_granola import AirbyteAuthConfig, GranolaConnector, Note


def get_connector() -> GranolaConnector:
    """Create a GranolaConnector in hosted execution mode.

    Connects to an existing hosted connector on Airbyte Cloud using
    customer_name lookup. Granola API credentials are managed server-side.
    """
    client_id = os.environ.get("AIRBYTE_CLIENT_ID")
    client_secret = os.environ.get("AIRBYTE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit(
            "Error: AIRBYTE_CLIENT_ID and AIRBYTE_CLIENT_SECRET environment variables must be set."
        )

    customer_name = os.environ.get("AIRBYTE_CUSTOMER_NAME", "patrick")

    return GranolaConnector(
        auth_config=AirbyteAuthConfig(
            customer_name=customer_name,
            airbyte_client_id=client_id,
            airbyte_client_secret=client_secret,
        )
    )


async def fetch_recent_notes(
    connector: GranolaConnector,
    days_back: int = 7,
) -> list[Note]:
    """Fetch recent meeting notes with full content (summary + transcript)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    # First, list recent note IDs
    note_ids: list[str] = []
    cursor = None

    while True:
        result = await connector.notes.list(
            created_after=cutoff_str,
            page_size=25,
            cursor=cursor,
        )

        for note in result.data or []:
            note_ids.append(note.id)

        if not result.meta.has_more:
            break
        cursor = result.meta.cursor

    # Then fetch full details for each note (includes summary + transcript)
    full_notes: list[Note] = []
    for note_id in note_ids:
        raw = await connector.notes.get(note_id=note_id, include="transcript")
        note = Note(**raw) if isinstance(raw, dict) else raw
        full_notes.append(note)

    return full_notes
