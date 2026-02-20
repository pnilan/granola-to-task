from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from dotenv import load_dotenv

from granola_to_task.agent import extract_action_items
from granola_to_task.source import fetch_recent_notes, get_connector


async def run(days: int) -> None:
    connector = get_connector()

    print(f"Fetching meeting notes from the last {days} day(s)...", file=sys.stderr)
    notes = await fetch_recent_notes(connector, days_back=days)

    if not notes:
        print("No meeting notes found.", file=sys.stderr)
        return

    print(f"Found {len(notes)} note(s). Analyzing for action items...\n", file=sys.stderr)

    all_results = []
    for note in notes:
        print(f"  Analyzing: {note.title or 'Untitled'}...", file=sys.stderr)
        result = await extract_action_items(note)
        if result.action_items:
            all_results.append(result)

    if not all_results:
        print("No action items found.")
        return

    for meeting in all_results:
        print(f"## {meeting.meeting_title} ({meeting.meeting_date})")
        for i, item in enumerate(meeting.action_items, 1):
            assignee = f" [@{item.assignee}]" if item.assignee else ""
            due = f" (due: {item.due_date})" if item.due_date else ""
            print(f"  {i}. {item.description}{assignee}{due}")
        print()


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Extract action items from recent Granola meeting notes.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for meeting notes (default: 7)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (includes HTTP requests)",
    )
    args = parser.parse_args()

    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    # Silence httpx unless --debug is passed
    if not args.debug:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    asyncio.run(run(args.days))
