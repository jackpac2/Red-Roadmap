from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class AlertWindow(QWidget):
    action_selected = Signal(str)

    def __init__(self, task: Dict[str, Any]) -> None:
        super().__init__()
        self.task = task
        self.setWindowTitle('RED ROADMAP ALERT')
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)

        snoozes = int(task.get('snooze_count') or 0)
        urgency = self._urgency_text(snoozes)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #050806;
                color: #f3ead7;
                font-family: Segoe UI;
            }
            QLabel#mission {
                font-size: 70px;
                font-weight: 800;
                color: #eadfb7;
            }
            QLabel#title {
                font-size: 52px;
                font-weight: 700;
                color: #f3ead7;
            }
            QLabel#urgency {
                font-size: 26px;
                font-weight: 600;
                color: #b7aa8a;
            }
            QFrame#statusPanel {
                background: #111a12;
                border: 2px solid #3a422f;
                border-radius: 12px;
            }
            QLabel#statusText {
                font-size: 20px;
                font-weight: 600;
            }
            QPushButton {
                font-size: 20px;
                font-weight: 700;
                padding: 14px 18px;
                border: 2px solid #3a422f;
                background-color: #1a2418;
                color: #f3ead7;
                border-radius: 8px;
            }
            QPushButton:hover {
                border-color: #eadfb7;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 60, 60, 60)
        root.setSpacing(28)

        mission = QLabel('MISSION ATTENTION REQUIRED')
        mission.setObjectName('mission')
        mission.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(task['title'])
        title.setObjectName('title')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        urgency_label = QLabel(urgency)
        urgency_label.setObjectName('urgency')
        urgency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_panel = QFrame()
        status_panel.setObjectName('statusPanel')
        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(16, 12, 16, 12)

        status_text = QLabel(f'SNOOZE COUNT: {snoozes}')
        status_text.setObjectName('statusText')
        status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(status_text)

        row = QHBoxLayout()
        row.setSpacing(16)

        start_btn = QPushButton('START NOW')
        snooze_btn = QPushButton('SNOOZE 10')
        away_btn = QPushButton('AWAY FROM PC')
        done_btn = QPushButton('MARK COMPLETE')

        start_btn.clicked.connect(lambda: self.action_selected.emit('start'))
        snooze_btn.clicked.connect(lambda: self.action_selected.emit('snooze_5'))
        away_btn.clicked.connect(lambda: self.action_selected.emit('away'))
        done_btn.clicked.connect(lambda: self.action_selected.emit('done'))

        row.addWidget(start_btn)
        row.addWidget(snooze_btn)
        row.addWidget(away_btn)
        row.addWidget(done_btn)

        root.addStretch(1)
        root.addWidget(mission)
        root.addWidget(title)
        root.addWidget(urgency_label)
        root.addWidget(status_panel)
        root.addLayout(row)
        root.addStretch(1)

    def show_alert(self) -> None:
        self.showFullScreen()
        self.activateWindow()
        self.raise_()

    @staticmethod
    def _urgency_text(snooze_count: int) -> str:
        if snooze_count <= 1:
            return 'Mission timing is active. Execute now.'
        if snooze_count <= 3:
            return 'Multiple snoozes detected. Immediate action recommended.'
        return 'Critical delay threshold reached. Start now.'
