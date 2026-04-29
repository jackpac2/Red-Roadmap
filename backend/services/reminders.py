from __future__ import annotations

from typing import Any, Optional


class ReminderService:
    def __init__(self, task_service: Any) -> None:
        self.task_service = task_service

    def get_next_attention_task(self) -> Optional[dict[str, Any]]:
        return self.task_service.get_next_attention_task()

    def get_due_reminders(self) -> list[dict[str, Any]]:
        return self.task_service.get_due_reminders()

    def snooze(self, task_id: int, minutes: int = 10) -> None:
        self.task_service.snooze_task(task_id, minutes)

    def apply_action(self, task_id: int, action: str) -> None:
        self.task_service.apply_alert_action(task_id, action)
