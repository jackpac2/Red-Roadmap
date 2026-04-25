from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from models import TaskRepository


class ReminderEngine(QObject):
    task_needs_attention = Signal(dict)

    def __init__(self, repo: TaskRepository, interval_ms: int = 10000) -> None:
        super().__init__()
        self.repo = repo
        self._alert_active = False
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.check_due_tasks)

    def start(self) -> None:
        self.timer.start()
        self.check_due_tasks()

    def pause_alerts(self) -> None:
        self._alert_active = True

    def resume_alerts(self) -> None:
        self._alert_active = False

    def check_due_tasks(self) -> None:
        if self._alert_active:
            return

        task: Optional[Dict[str, Any]] = self.repo.get_next_attention_task()
        if task:
            self._alert_active = True
            self.task_needs_attention.emit(task)
