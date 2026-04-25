from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TaskCard(QFrame):
    task_toggled = Signal(int, bool)
    micro_toggled = Signal(int, bool)
    add_micro = Signal(int, str)
    delete_micro = Signal(int)
    edit_micro = Signal(int, str)
    delete_task = Signal(int)
    start_task = Signal(int)
    selection_toggled = Signal(int, bool)
    expand_changed = Signal(int, bool)

    def __init__(
        self,
        task: Dict[str, Any],
        selection_mode: bool = False,
        expanded: bool = False,
    ) -> None:
        super().__init__()
        self.task = task
        self.selection_mode = selection_mode
        self.is_expanded = expanded

        self.setObjectName('taskCard')
        self.setFrameShape(QFrame.StyledPanel)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.select_box = QCheckBox()
        self.select_box.setVisible(selection_mode)
        self.select_box.toggled.connect(
            lambda checked: self.selection_toggled.emit(int(self.task['id']), checked)
        )

        self.complete_box = QCheckBox()
        self.complete_box.setChecked(task['status'] == 'COMPLETED')
        self.complete_box.toggled.connect(self._on_task_toggled)

        self.title_label = QLabel(task['title'])
        self.title_label.setObjectName('taskTitle')

        priority = QLabel(f"PRIORITY: {task['priority']}")
        priority.setObjectName(f"priority{task['priority']}")

        mode_map = {'AT_PC': 'AT PC', 'AWAY': 'AWAY', 'FLEXIBLE': 'FLEXIBLE'}
        mode_text = mode_map.get(task['mode'], task['mode'])
        mode = QLabel(f'MODE: {mode_text}')
        mode.setObjectName('modeBadge')

        status = QLabel(f"STATUS: {task['status']}")
        status.setObjectName('statusBadge')

        reminder = QLabel(self._format_reminder(task.get('reminder_at')))
        reminder.setObjectName('reminderText')

        top_row.addWidget(self.select_box)
        top_row.addWidget(self.complete_box)
        top_row.addWidget(self.title_label, 1)
        top_row.addWidget(priority)
        top_row.addWidget(mode)
        top_row.addWidget(status)
        top_row.addWidget(reminder)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.start_btn = QPushButton('Start')
        self.start_btn.clicked.connect(lambda: self.start_task.emit(int(self.task['id'])))

        self.expand_btn = QPushButton('Hide Steps' if expanded else 'Expand Steps')
        self.expand_btn.clicked.connect(self.toggle_expanded)

        self.complete_btn = QPushButton('Complete')
        self.complete_btn.clicked.connect(lambda: self.task_toggled.emit(int(self.task['id']), True))

        self.delete_btn = QPushButton('Delete')
        self.delete_btn.clicked.connect(lambda: self.delete_task.emit(int(self.task['id'])))

        action_row.addWidget(self.start_btn)
        action_row.addWidget(self.expand_btn)
        action_row.addWidget(self.complete_btn)
        action_row.addWidget(self.delete_btn)
        action_row.addStretch(1)

        root.addLayout(top_row)
        root.addLayout(action_row)

        self.details = QWidget()
        self.details_layout = QVBoxLayout(self.details)
        self.details_layout.setContentsMargins(12, 4, 0, 0)
        self.details_layout.setSpacing(6)

        self._render_micro_actions(task.get('micro_actions', []))

        add_row = QHBoxLayout()
        self.new_micro_input = QLineEdit()
        self.new_micro_input.setPlaceholderText('Add mission step...')
        self.new_micro_input.returnPressed.connect(self._on_add_micro)
        add_micro_btn = QPushButton('Add Step')
        add_micro_btn.clicked.connect(self._on_add_micro)
        add_row.addWidget(self.new_micro_input, 1)
        add_row.addWidget(add_micro_btn)

        self.details_layout.addLayout(add_row)
        self.details.setVisible(self.is_expanded)
        root.addWidget(self.details)

    def set_selection_mode(self, enabled: bool) -> None:
        self.selection_mode = enabled
        self.select_box.setVisible(enabled)
        if not enabled:
            self.select_box.setChecked(False)

    def set_expanded(self, expanded: bool) -> None:
        self.is_expanded = expanded
        self.details.setVisible(expanded)
        self.expand_btn.setText('Hide Steps' if expanded else 'Expand Steps')

    def toggle_expanded(self) -> None:
        self.set_expanded(not self.is_expanded)
        self.expand_changed.emit(int(self.task['id']), self.is_expanded)

    def focus_micro_input(self) -> None:
        self.new_micro_input.setFocus()

    def _render_micro_actions(self, micro_actions: List[Dict[str, Any]]) -> None:
        for item in micro_actions:
            row = QHBoxLayout()
            row.setSpacing(6)

            box = QCheckBox()
            box.setChecked(bool(item['completed']))
            box.toggled.connect(
                lambda checked, micro_id=int(item['id']): self.micro_toggled.emit(micro_id, checked)
            )

            title = QLabel(item['title'])
            title.setObjectName('microTitle')

            edit_btn = QPushButton('Edit')
            edit_btn.clicked.connect(
                lambda _=False, micro_id=int(item['id']), text=item['title']:
                self.edit_micro.emit(micro_id, text)
            )

            del_btn = QPushButton('Delete')
            del_btn.clicked.connect(
                lambda _=False, micro_id=int(item['id']): self.delete_micro.emit(micro_id)
            )

            row.addWidget(box)
            row.addWidget(title, 1)
            row.addWidget(edit_btn)
            row.addWidget(del_btn)

            self.details_layout.addLayout(row)

    def _on_task_toggled(self, checked: bool) -> None:
        self.task_toggled.emit(int(self.task['id']), checked)

    def _on_add_micro(self) -> None:
        title = self.new_micro_input.text().strip()
        if not title:
            self.new_micro_input.setFocus()
            return
        self.add_micro.emit(int(self.task['id']), title)
        self.new_micro_input.clear()
        self.new_micro_input.setFocus()

    @staticmethod
    def _format_reminder(reminder_at: Any) -> str:
        if not reminder_at:
            return 'REMINDER: None'

        if isinstance(reminder_at, datetime):
            return f"REMINDER: {reminder_at.strftime('%Y-%m-%d %H:%M')}"
        return f'REMINDER: {reminder_at}'
