from __future__ import annotations

from typing import Any

from airbyte_agent_granola import Note
from pydantic_ai import Agent

from granola_to_task.models import MeetingActionItems

SYSTEM_PROMPT = (
    "You are an expert at analyzing meeting notes and extracting action items. "
    "Given a meeting note, identify all action items, tasks, follow-ups, and commitments. "
    "For each action item, extract:\n"
    "- A clear, concise description of what needs to be done\n"
    "- The assignee (person responsible), if mentioned by name\n"
    "- A due date or deadline, if mentioned\n"
    "\n"
    "Only extract concrete, actionable items. Do not invent action items that aren't "
    "clearly stated or strongly implied in the notes. If there are no action items, "
    "return an empty list."
)


def _get_agent() -> Agent[None, MeetingActionItems]:
    return Agent(
        "anthropic:claude-sonnet-4-6",
        system_prompt=SYSTEM_PROMPT,
        output_type=MeetingActionItems,
    )


def _get_name(obj: Any) -> str:
    """Extract a name from an object that may be a Pydantic model or a dict."""
    if isinstance(obj, dict):
        return obj.get("name") or obj.get("email") or "Unknown"
    return getattr(obj, "name", None) or getattr(obj, "email", None) or "Unknown"


def _format_note_for_analysis(note: Note) -> str:
    """Format a Granola note into a text prompt for the agent."""
    parts = [f"Meeting: {note.title or 'Untitled'}"]
    parts.append(f"Date: {note.created_at or 'Unknown'}")

    if note.attendees:
        names = [_get_name(a) for a in note.attendees]
        parts.append(f"Attendees: {', '.join(names)}")

    summary = note.summary_markdown or note.summary_text
    if summary:
        parts.append(f"\n## Summary\n{summary}")

    if note.transcript:
        lines = []
        for entry in note.transcript:
            if isinstance(entry, dict):
                speaker = entry.get("speaker")
                text = entry.get("text", "")
            else:
                speaker = entry.speaker
                text = getattr(entry, "text", "")
            speaker_name = _get_name(speaker) if speaker else "Unknown"
            lines.append(f"{speaker_name}: {text}")
        parts.append("\n## Transcript\n" + "\n".join(lines))

    return "\n".join(parts)


async def extract_action_items(note: Note) -> MeetingActionItems:
    """Extract action items from a single meeting note."""
    agent = _get_agent()
    prompt = _format_note_for_analysis(note)
    result = await agent.run(prompt)
    return result.output
