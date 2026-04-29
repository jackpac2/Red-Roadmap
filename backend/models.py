from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Mode(str, Enum):
    AT_PC = "AT_PC"
    AWAY = "AWAY"
    FLEXIBLE = "FLEXIBLE"


class Status(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    AWAY = "AWAY"
    COMPLETED = "COMPLETED"


class AlertAction(str, Enum):
    start = "start"
    snooze_5 = "snooze_5"
    snooze_15 = "snooze_15"
    away = "away"
    done = "done"


class Step(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    title: str
    completed: bool
    completed_at: Optional[datetime] = None
    sort_order: int = 0


class Mission(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: Priority
    mode: Mode
    status: Status
    reminder_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    last_progress_at: Optional[datetime] = None
    snooze_count: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    micro_actions: list[Step] = Field(default_factory=list)


class MissionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    priority: Priority = Priority.MEDIUM
    mode: Mode = Mode.FLEXIBLE
    reminder_at: Optional[datetime] = None


class MissionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    priority: Priority
    mode: Mode
    reminder_at: Optional[datetime] = None


class MissionPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    priority: Optional[Priority] = None
    mode: Optional[Mode] = None
    status: Optional[Status] = None
    reminder_at: Optional[datetime] = None
    clear_reminder: bool = False


class StepCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class StepUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class CompleteRequest(BaseModel):
    completed: bool = True


class SnoozeRequest(BaseModel):
    minutes: int = Field(default=10, ge=1, le=240)


class ReminderUpdate(BaseModel):
    reminder_at: datetime


class AlertActionRequest(BaseModel):
    action: AlertAction


class DashboardStats(BaseModel):
    active_tasks: int
    pending_tasks: int
    completed_tasks: int
    away_tasks: int
    snoozed_tasks: int


class ProgressSummary(BaseModel):
    total: int
    completed: int
    percent: int


class ExecutionScore(BaseModel):
    score: int


class TimelineItem(BaseModel):
    id: int
    title: str
    status: Status
    priority: Priority
    reminder_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    created_at: datetime


class DashboardSummary(BaseModel):
    stats: DashboardStats
    progress: ProgressSummary
    execution_score: int
    timeline: list[TimelineItem]
