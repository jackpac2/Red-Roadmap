from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Set

from mysql.connector import Error
from PySide6.QtCore import QDateTime, QTimer, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from audio import AnnoyingAudioPlayer
from models import TaskRepository
from reminder_engine import ReminderEngine
from ui.alert_window import AlertWindow
from ui.task_card import TaskCard


class MainWindow(QWidget):
    def __init__(self, repo: TaskRepository, reminder_engine: ReminderEngine) -> None:
        super().__init__()
        self.repo = repo
        self.reminder_engine = reminder_engine
        self.audio = AnnoyingAudioPlayer()
        self.current_alert: Optional[AlertWindow] = None
        self.current_alert_task_id: Optional[int] = None
        self.current_active_task_id: Optional[int] = None

        self.selection_mode = False
        self.focus_mode = False
        self.selected_task_ids: Set[int] = set()
        self.expanded_task_ids: Set[int] = set()
        self.task_cards: Dict[int, TaskCard] = {}
        self.task_lookup: Dict[int, dict] = {}
        self._pending_micro_focus_task_id: Optional[int] = None

        self.setWindowTitle('Red Roadmap')
        self.resize(1480, 900)
        self.setStyleSheet(self._styles())

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        left_panel = QFrame()
        left_panel.setObjectName('timelinePanel')
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        timeline_title = QLabel('Roadmap Timeline')
        timeline_title.setObjectName('sectionTitle')
        self.timeline_list = QListWidget()

        left_layout.addWidget(timeline_title)
        left_layout.addWidget(self.timeline_list, 1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        right_layout.addWidget(self._build_header())
        right_layout.addWidget(self._build_progress_card())
        right_layout.addWidget(self._build_basic_stats())
        right_layout.addLayout(self._build_actions_row())

        missions_title = QLabel('Mission List')
        missions_title.setObjectName('sectionTitle')
        right_layout.addWidget(missions_title)
        right_layout.addWidget(self._build_task_scroll(), 8)

        root.addWidget(left_panel, 2)
        root.addWidget(right_panel, 8)

        self.reminder_engine.task_needs_attention.connect(self._show_alert_for_task)

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start()
        self._update_clock()

        self.refresh()

    def _build_header(self) -> QFrame:
        top_bar = QFrame()
        top_bar.setObjectName('topBar')
        top_bar.setMaximumHeight(92)
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(12, 10, 12, 10)

        left_col = QVBoxLayout()
        self.header = QLabel('RED ROADMAP')
        self.header.setObjectName('appTitle')
        self.subtitle = QLabel('Track your journey, one task at a time')
        self.subtitle.setObjectName('subtitle')
        left_col.addWidget(self.header)
        left_col.addWidget(self.subtitle)

        right_col = QVBoxLayout()
        self.datetime_label = QLabel('0000-00-00 00:00:00')
        self.datetime_label.setObjectName('clockText')
        self.execution_score = QLabel("Today's Execution Score: 0%")
        self.execution_score.setObjectName('clockText')
        right_col.addWidget(self.datetime_label)
        right_col.addWidget(self.execution_score)

        layout.addLayout(left_col, 1)
        layout.addLayout(right_col)
        return top_bar

    def _build_progress_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName('progressCard')
        card.setMaximumHeight(88)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self.progress_text = QLabel('0 / 0 completed (0%)')
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        layout.addWidget(self.progress_text)
        layout.addWidget(self.progress_bar)
        return card

    def _build_basic_stats(self) -> QFrame:
        card = QFrame()
        card.setObjectName('statsCard')
        card.setMaximumHeight(60)

        row = QHBoxLayout(card)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(14)

        self.active_label = QLabel('Active: 0')
        self.pending_label = QLabel('Pending: 0')
        self.completed_label = QLabel('Completed: 0')
        self.away_label = QLabel('Away: 0')
        self.snoozed_label = QLabel('Snoozed: 0')

        for label in [
            self.active_label,
            self.pending_label,
            self.completed_label,
            self.away_label,
            self.snoozed_label,
        ]:
            label.setObjectName('statText')
            row.addWidget(label)
        row.addStretch(1)
        return card

    def _build_actions_row(self) -> QHBoxLayout:
        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.add_btn = QPushButton('Add Mission')
        self.paste_btn = QPushButton('Paste Missions')
        self.focus_btn = QPushButton('Focus Mode')
        self.select_btn = QPushButton('Select Multiple')
        self.delete_all_btn = QPushButton('Delete All')

        self.add_btn.clicked.connect(self.open_add_task_dialog)
        self.paste_btn.clicked.connect(self.open_paste_dialog)
        self.focus_btn.clicked.connect(self.toggle_focus_mode)
        self.select_btn.clicked.connect(self.toggle_selection_mode)
        self.delete_all_btn.clicked.connect(self.delete_all_tasks)

        actions.addWidget(self.add_btn)
        actions.addWidget(self.paste_btn)
        actions.addWidget(self.focus_btn)
        actions.addWidget(self.select_btn)
        actions.addWidget(self.delete_all_btn)
        actions.addStretch(1)
        return actions

    def _build_task_scroll(self) -> QScrollArea:
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(10)
        self.task_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.task_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(520)
        return scroll

    def refresh(self) -> None:
        try:
            tasks = self.repo.fetch_tasks()
            totals = self.repo.get_totals()
            stats = self.repo.get_dashboard_stats()
            execution_score = self.repo.get_today_execution_score()
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to load dashboard:\n{exc}')
            return

        current_ids = {int(task['id']) for task in tasks}
        self.expanded_task_ids.intersection_update(current_ids)
        self.task_lookup = {int(task['id']): task for task in tasks}

        self._render_timeline(tasks)
        self._render_tasks(tasks)

        total = totals['total']
        completed = totals['completed']
        pct = int((completed / total) * 100) if total else 0
        self.progress_text.setText(f'{completed} / {total} completed ({pct}%)')
        self.progress_bar.setValue(pct)

        self.active_label.setText(f"Active: {stats['active_tasks']}")
        self.pending_label.setText(f"Pending: {stats['pending_tasks']}")
        self.completed_label.setText(f"Completed: {stats['completed_tasks']}")
        self.away_label.setText(f"Away: {stats['away_tasks']}")
        self.snoozed_label.setText(f"Snoozed: {stats['snoozed_tasks']}")

        self.execution_score.setText(f"Today's Execution Score: {execution_score}%")

    def _render_timeline(self, tasks: list[dict]) -> None:
        self.timeline_list.clear()
        for task in tasks:
            marker = self._status_marker(task['status'])
            item = QListWidgetItem(f"{marker} {task['title']}")
            self.timeline_list.addItem(item)

    def _render_tasks(self, tasks: list[dict]) -> None:
        self.task_cards.clear()
        while self.task_layout.count():
            item = self.task_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        filtered = tasks
        if self.focus_mode:
            filtered = [t for t in tasks if t['status'] in ('PENDING', 'ACTIVE')]

        for task in filtered:
            task_id = int(task['id'])
            card = TaskCard(
                task,
                selection_mode=self.selection_mode,
                expanded=task_id in self.expanded_task_ids,
            )
            card.task_toggled.connect(self.on_task_toggled)
            card.micro_toggled.connect(self.on_micro_toggled)
            card.add_micro.connect(self.on_add_micro)
            card.delete_micro.connect(self.on_delete_micro)
            card.edit_micro.connect(self.on_edit_micro)
            card.edit_task.connect(self.on_edit_task)
            card.delete_task.connect(self.on_delete_task)
            card.start_task.connect(self.on_start_task)
            card.selection_toggled.connect(self.on_selection_changed)
            card.expand_changed.connect(self.on_expand_changed)
            self.task_layout.addWidget(card)
            self.task_cards[task_id] = card

        self.task_layout.addStretch(1)

        if self._pending_micro_focus_task_id is not None:
            task_id = self._pending_micro_focus_task_id
            card = self.task_cards.get(task_id)
            if card and task_id in self.expanded_task_ids:
                QTimer.singleShot(0, card.focus_micro_input)
            self._pending_micro_focus_task_id = None

    def open_add_task_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Mission')
        form = QFormLayout(dialog)

        title = QLineEdit()
        priority = QComboBox()
        priority.addItems(['LOW', 'MEDIUM', 'HIGH'])
        mode = QComboBox()
        mode.addItems(['AT_PC', 'AWAY', 'FLEXIBLE'])
        reminder_check = QCheckBox('Set reminder')
        reminder = QDateTimeEdit(QDateTime.currentDateTime())
        reminder.setCalendarPopup(True)
        reminder.setDisplayFormat('yyyy-MM-dd HH:mm')
        reminder.setEnabled(False)
        reminder_check.toggled.connect(reminder.setEnabled)

        save = QPushButton('Save')
        cancel = QPushButton('Cancel')
        save.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)

        btn_row = QHBoxLayout()
        btn_row.addWidget(save)
        btn_row.addWidget(cancel)

        form.addRow('Title', title)
        form.addRow('Priority', priority)
        form.addRow('Mode', mode)
        form.addRow('', reminder_check)
        form.addRow('Reminder', reminder)
        form.addRow(btn_row)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        task_title = title.text().strip()
        if not task_title:
            QMessageBox.warning(self, 'Validation', 'Task title is required.')
            return

        reminder_at = reminder.dateTime().toPython() if reminder_check.isChecked() else None

        try:
            self.repo.add_task(task_title, priority.currentText(), mode.currentText(), reminder_at)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to add task:\n{exc}')
            return

        self.refresh()

    def open_paste_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle('Paste Missions')
        layout = QVBoxLayout(dialog)

        editor = QTextEdit()
        editor.setPlaceholderText('One mission per line...')
        layout.addWidget(editor)

        row = QHBoxLayout()
        save = QPushButton('Add Missions')
        cancel = QPushButton('Cancel')
        save.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        row.addWidget(save)
        row.addWidget(cancel)
        layout.addLayout(row)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            count = self.repo.add_tasks_from_lines(editor.toPlainText().splitlines())
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to add tasks:\n{exc}')
            return

        QMessageBox.information(self, 'Missions Added', f'Added {count} missions.')
        self.refresh()

    def toggle_focus_mode(self) -> None:
        self.focus_mode = not self.focus_mode
        self.focus_btn.setText('Focus Mode ON' if self.focus_mode else 'Focus Mode')
        self.refresh()

    def toggle_selection_mode(self) -> None:
        self.selection_mode = not self.selection_mode
        self.selected_task_ids.clear()
        self.select_btn.setText('Cancel Select' if self.selection_mode else 'Select Multiple')
        self.refresh()

    def on_selection_changed(self, task_id: int, selected: bool) -> None:
        if selected:
            self.selected_task_ids.add(task_id)
        else:
            self.selected_task_ids.discard(task_id)

    def on_expand_changed(self, task_id: int, expanded: bool) -> None:
        if expanded:
            self.expanded_task_ids.add(task_id)
        else:
            self.expanded_task_ids.discard(task_id)

    def delete_all_tasks(self) -> None:
        reply = QMessageBox.question(
            self,
            'Delete All',
            'Delete all tasks and micro-actions?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.repo.delete_all_tasks()
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to delete tasks:\n{exc}')
            return

        self.expanded_task_ids.clear()
        self.refresh()

    def on_delete_task(self, task_id: int) -> None:
        reply = QMessageBox.question(
            self,
            'Delete Task',
            'Delete this task and all its micro-actions?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.repo.delete_task(task_id)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to delete task:\n{exc}')
            return

        self.expanded_task_ids.discard(task_id)
        self.refresh()

    def on_edit_task(self, task_id: int) -> None:
        task = self.task_lookup.get(task_id)
        if not task:
            QMessageBox.warning(self, 'Task Not Found', 'Could not load this task for editing.')
            return

        dialog = QDialog(self)
        dialog.setWindowTitle('Edit Mission')
        form = QFormLayout(dialog)

        title = QLineEdit(str(task['title']))
        priority = QComboBox()
        priority.addItems(['LOW', 'MEDIUM', 'HIGH'])
        priority.setCurrentText(str(task['priority']))

        mode = QComboBox()
        mode.addItems(['AT_PC', 'AWAY', 'FLEXIBLE'])
        mode.setCurrentText(str(task['mode']))

        reminder_check = QCheckBox('Set reminder')
        reminder = QDateTimeEdit(QDateTime.currentDateTime())
        reminder.setCalendarPopup(True)
        reminder.setDisplayFormat('yyyy-MM-dd HH:mm')

        reminder_value = task.get('reminder_at')
        if isinstance(reminder_value, datetime):
            reminder.setDateTime(QDateTime(reminder_value))
            reminder_check.setChecked(True)
            reminder.setEnabled(True)
        else:
            reminder_check.setChecked(False)
            reminder.setEnabled(False)

        reminder_check.toggled.connect(reminder.setEnabled)

        save = QPushButton('Save')
        cancel = QPushButton('Cancel')
        save.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)

        btn_row = QHBoxLayout()
        btn_row.addWidget(save)
        btn_row.addWidget(cancel)

        form.addRow('Title', title)
        form.addRow('Priority', priority)
        form.addRow('Mode', mode)
        form.addRow('', reminder_check)
        form.addRow('Reminder', reminder)
        form.addRow(btn_row)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        updated_title = title.text().strip()
        if not updated_title:
            QMessageBox.warning(self, 'Validation', 'Task title is required.')
            return

        reminder_at = reminder.dateTime().toPython() if reminder_check.isChecked() else None

        try:
            self.repo.update_task(
                task_id,
                updated_title,
                priority.currentText(),
                mode.currentText(),
                reminder_at,
            )
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to update task:\n{exc}')
            return

        self.refresh()

    def on_task_toggled(self, task_id: int, completed: bool) -> None:
        try:
            self.repo.set_task_completed(task_id, completed)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to update task:\n{exc}')
            return
        self.refresh()

    def on_start_task(self, task_id: int) -> None:
        try:
            self.repo.start_task(task_id)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to start task:\n{exc}')
            return
        self.refresh()

    def on_micro_toggled(self, micro_id: int, completed: bool) -> None:
        try:
            task_id = self.repo.set_micro_completed(micro_id, completed)
            if task_id:
                self.expanded_task_ids.add(task_id)

            if task_id and completed and self.repo.all_micro_complete(task_id):
                reply = QMessageBox.question(
                    self,
                    'Micro-actions complete',
                    'All micro-actions are complete. Mark the whole task as done?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.repo.set_task_completed(task_id, True)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to update micro-action:\n{exc}')
            return
        self.refresh()

    def on_add_micro(self, task_id: int, title: str) -> None:
        try:
            self.repo.add_micro_action(task_id, title)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to add micro-action:\n{exc}')
            return

        self.expanded_task_ids.add(task_id)
        self._pending_micro_focus_task_id = task_id
        self.refresh()

    def on_delete_micro(self, micro_id: int) -> None:
        try:
            self.repo.delete_micro_action(micro_id)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to delete micro-action:\n{exc}')
            return
        self.refresh()

    def on_edit_micro(self, micro_id: int, current_title: str) -> None:
        text, ok = QInputDialog.getText(self, 'Edit Mission Step', 'Title', text=current_title)
        if not ok:
            return

        title = text.strip()
        if not title:
            return

        try:
            self.repo.update_micro_action_title(micro_id, title)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to edit micro-action:\n{exc}')
            return
        self.refresh()

    def _show_alert_for_task(self, task: Dict[str, object]) -> None:
        self.current_alert_task_id = int(task['id'])

        if self.current_alert:
            self.current_alert.close()

        self.current_alert = AlertWindow(task)
        self.current_alert.action_selected.connect(self._handle_alert_action)

        intensity = self._intensity_from_snooze(int(task.get('snooze_count') or 0))
        self.audio.start_loop(intensity)
        self.current_alert.show_alert()

    def _handle_alert_action(self, action: str) -> None:
        if self.current_alert_task_id is None:
            return

        try:
            self.repo.apply_alert_action(self.current_alert_task_id, action)
        except Error as exc:
            QMessageBox.critical(self, 'Database Error', f'Failed to apply action:\n{exc}')
            return
        finally:
            self.audio.stop()

        if self.current_alert:
            self.current_alert.close()
            self.current_alert = None

        self.current_alert_task_id = None
        self.reminder_engine.resume_alerts()
        self.refresh()

    def _update_clock(self) -> None:
        self.datetime_label.setText(QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss'))

    @staticmethod
    def _status_marker(status: str) -> str:
        mapping = {'PENDING': '[P]', 'ACTIVE': '[A]', 'AWAY': '[W]', 'COMPLETED': '[C]'}
        return mapping.get(status, '[?]')

    @staticmethod
    def _intensity_from_snooze(snooze_count: int) -> int:
        if snooze_count <= 1:
            return 1
        if snooze_count <= 3:
            return 2
        return 3

    @staticmethod
    def _styles() -> str:
        return """
        QWidget {
            background: #050713;
            color: #eaf1ff;
            font-family: 'Segoe UI';
        }
        QFrame#timelinePanel, QFrame#topBar, QFrame#progressCard, QFrame#statsCard, QFrame#taskCard {
            background: #0a1020;
            border: 1px solid #2f3b66;
            border-radius: 12px;
        }
        QLabel#appTitle {
            font-size: 40px;
            font-weight: 800;
            color: #ff4fcf;
        }
        QLabel#subtitle {
            font-size: 14px;
            color: #9ab6de;
        }
        QLabel#clockText {
            font-size: 12px;
            color: #bcd6ff;
        }
        QLabel#sectionTitle {
            font-size: 20px;
            font-weight: 700;
            color: #cfe2ff;
        }
        QLabel#statText {
            font-size: 12px;
            font-weight: 700;
            color: #bcd6ff;
        }
        QLabel#taskTitle {
            font-size: 16px;
            font-weight: 700;
            color: #f2f6ff;
        }
        QLabel#microTitle {
            color: #d6e7ff;
        }
        QLabel#priorityLOW,
        QLabel#priorityMEDIUM,
        QLabel#priorityHIGH,
        QLabel#modeBadge,
        QLabel#statusBadge {
            border-radius: 6px;
            padding: 3px 8px;
            border: 1px solid #42558b;
            background: #101a35;
            color: #b9d4ff;
        }
        QLabel#priorityHIGH {
            border: 1px solid #ff5d7d;
            color: #ffdbe4;
            background: #2f0f1a;
        }
        QLabel#reminderText {
            color: #aec7ef;
        }
        QPushButton {
            background: #131f3f;
            border: 1px solid #4a61a3;
            border-radius: 8px;
            padding: 8px 10px;
            color: #f0f6ff;
            font-weight: 600;
        }
        QPushButton:hover {
            background: #1a2a57;
            border: 1px solid #66e7ff;
        }
        QLineEdit, QTextEdit, QDateTimeEdit, QComboBox, QListWidget {
            background: #081127;
            border: 1px solid #3a4f86;
            border-radius: 6px;
            padding: 6px;
            color: #ecf4ff;
        }
        QProgressBar {
            border: 1px solid #3c548d;
            border-radius: 6px;
            text-align: center;
            background: #071127;
            color: #f2f6ff;
        }
        QProgressBar::chunk {
            background-color: #ff4fcf;
            border-radius: 6px;
        }
        """
