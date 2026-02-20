from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from airbyte_agent_granola import AirbyteAuthConfig, GranolaAuthConfig, GranolaConnector, Note

logger = logging.getLogger(__name__)


def get_connector() -> GranolaConnector:
    """Create a GranolaConnector, auto-detecting execution mode from env vars.

    Hosted mode (preferred): AIRBYTE_CLIENT_ID + AIRBYTE_CLIENT_SECRET are set.
    Local mode (fallback):   GRANOLA_API_KEY is set.
    """
    client_id = os.environ.get("AIRBYTE_CLIENT_ID")
    client_secret = os.environ.get("AIRBYTE_CLIENT_SECRET")
    if client_id and client_secret:
        customer_name = os.environ.get("AIRBYTE_CUSTOMER_NAME", "patrick")
        logger.info("Using hosted execution mode (customer=%s)", customer_name)
        return GranolaConnector(
            auth_config=AirbyteAuthConfig(
                customer_name=customer_name,
                airbyte_client_id=client_id,
                airbyte_client_secret=client_secret,
            )
        )

    api_key = os.environ.get("GRANOLA_API_KEY")
    if api_key:
        logger.info("Using local execution mode")
        return GranolaConnector(auth_config=GranolaAuthConfig(api_key=api_key))

    raise SystemExit(
        "Error: No Granola credentials found.\n"
        "Set AIRBYTE_CLIENT_ID + AIRBYTE_CLIENT_SECRET for hosted mode, or\n"
        "set GRANOLA_API_KEY for local mode."
    )


async def _search_note_ids(
    connector: GranolaConnector,
    cutoff_iso: str,
) -> list[str]:
    """Search for recent note IDs using the hosted search index."""
    note_ids: list[str] = []
    cursor = None
    page = 0

    while True:
        page += 1
        query = {
            "filter": {"gte": {"created_at": cutoff_iso}},
            "sort": [{"created_at": "desc"}],
        }
        params = {"query": query, "limit": 25, "cursor": cursor, "fields": [["id"]]}
        logger.info("notes.search: page=%d, params=%s", page, params)

        result = await connector.notes.search(
            query=query,
            limit=25,
            cursor=cursor,
            fields=[["id"]],
        )
        logger.info(
            "notes.search: page=%d returned %d result(s), has_more=%s",
            page,
            len(result.data),
            result.meta.has_more,
        )

        for record in result.data:
            if record.id:
                note_ids.append(record.id)

        if not result.meta.has_more:
            break
        cursor = result.meta.cursor

    return note_ids


async def _list_note_ids(
    connector: GranolaConnector,
    cutoff_date: str,
) -> list[str]:
    """Fall back to the list action to find recent note IDs."""
    note_ids: list[str] = []
    cursor = None
    page = 0

    while True:
        page += 1
        params = {"created_after": cutoff_date, "page_size": 25, "cursor": cursor}
        logger.info("notes.list: page=%d, params=%s", page, params)

        result = await connector.notes.list(
            created_after=cutoff_date,
            page_size=25,
            cursor=cursor,
        )

        batch = result.data or []
        logger.info(
            "notes.list: page=%d returned %d result(s), has_more=%s",
            page,
            len(batch),
            result.meta.has_more,
        )

        for note in batch:
            note_ids.append(note.id)

        if not result.meta.has_more:
            break
        cursor = result.meta.cursor

    return note_ids


async def fetch_recent_notes(
    connector: GranolaConnector,
    days_back: int = 7,
) -> list[Note]:
    """Fetch recent meeting notes with full content (summary + transcript).

    Prioritizes the search action (faster, indexed). If search returns no
    results (e.g. index lag for very recent notes), falls back to the list action.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    note_ids: list[str] = []
    try:
        note_ids = await _search_note_ids(connector, cutoff.isoformat())
    except NotImplementedError:
        logger.info("Search not available (local mode), using list action")

    if not note_ids:
        logger.info("Falling back to list action")
        note_ids = await _list_note_ids(connector, cutoff.strftime("%Y-%m-%d"))

    logger.info("Fetching full details for %d note(s)", len(note_ids))

    # Fetch full details for each note (includes summary + transcript)
    full_notes: list[Note] = []
    for note_id in note_ids:
        params = {"note_id": note_id, "include": "transcript"}
        logger.info("notes.get: params=%s", params)
        raw = await connector.notes.get(note_id=note_id, include="transcript")
        note = Note(**raw) if isinstance(raw, dict) else raw
        full_notes.append(note)

    return full_notes
