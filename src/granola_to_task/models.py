from __future__ import annotations

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """A single action item extracted from a meeting note."""

    description: str = Field(description="What needs to be done")
    assignee: str | None = Field(
        default=None, description="Person responsible, if mentioned"
    )
    due_date: str | None = Field(
        default=None, description="Deadline or target date, if mentioned"
    )
    source_meeting: str = Field(description="Title of the meeting this came from")


class MeetingActionItems(BaseModel):
    """Action items extracted from a single meeting note."""

    meeting_title: str
    meeting_date: str
    action_items: list[ActionItem] = Field(default_factory=list)
