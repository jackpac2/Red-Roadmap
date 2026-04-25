from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget


class MetricCard(QFrame):
    def __init__(self, title: str, accent: str) -> None:
        super().__init__()
        self.setObjectName('metricCard')
        self.setProperty('accent', accent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName('metricTitle')

        self.value_label = QLabel('0')
        self.value_label.setObjectName('metricValue')

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class BreakdownWidget(QFrame):
    def __init__(self, title: str, colors: Dict[str, str]) -> None:
        super().__init__()
        self.setObjectName('chartCard')
        self._bars: Dict[str, QProgressBar] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName('chartTitle')
        layout.addWidget(title_label)

        for key, color in colors.items():
            row = QHBoxLayout()
            row.setSpacing(6)

            label = QLabel(key)
            label.setObjectName('chartLabel')
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setFormat('%v')
            bar.setStyleSheet(
                f"""
                QProgressBar {{
                    border: 1px solid #385069;
                    border-radius: 6px;
                    background: #08111a;
                    color: #dcecff;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background: {color};
                    border-radius: 6px;
                }}
                """
            )
            row.addWidget(label)
            row.addWidget(bar, 1)
            layout.addLayout(row)
            self._bars[key] = bar

    def set_data(self, values: Dict[str, int]) -> None:
        max_value = max(1, max(values.values()) if values else 1)
        for key, bar in self._bars.items():
            v = int(values.get(key, 0))
            bar.setRange(0, max_value)
            bar.setValue(v)


class MiniBarChart(QFrame):
    def __init__(self, title: str, bar_color: str = '#00e5ff') -> None:
        super().__init__()
        self.setObjectName('chartCard')
        self._values: List[Dict[str, int | str]] = []
        self._bar_color = bar_color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName('chartTitle')
        layout.addWidget(title_label)

        self.chart = _MiniBarCanvas(bar_color)
        layout.addWidget(self.chart, 1)

    def set_values(self, values: List[Dict[str, int | str]]) -> None:
        self._values = values
        self.chart.set_values(values)


class _MiniBarCanvas(QWidget):
    def __init__(self, bar_color: str) -> None:
        super().__init__()
        self._values: List[Dict[str, int | str]] = []
        self._bar_color = QColor(bar_color)
        self.setMinimumHeight(120)

    def set_values(self, values: List[Dict[str, int | str]]) -> None:
        self._values = values
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(8, 8, -8, -22)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter.fillRect(rect, QColor('#08111a'))

        if not self._values:
            painter.setPen(QColor('#8da7bf'))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, 'No data')
            return

        max_val = max(1, max(int(item.get('value', 0)) for item in self._values))
        bar_gap = 8
        bar_width = max(8, int((rect.width() - bar_gap * (len(self._values) - 1)) / len(self._values)))

        x = rect.left()
        for item in self._values:
            value = int(item.get('value', 0))
            label = str(item.get('label', ''))
            bar_h = int((value / max_val) * (rect.height() - 10))
            bar_rect = QRect(x, rect.bottom() - bar_h, bar_width, bar_h)
            painter.fillRect(bar_rect, self._bar_color)
            painter.setPen(QColor('#cae8ff'))
            painter.drawText(x, rect.bottom() + 14, bar_width, 14, Qt.AlignmentFlag.AlignCenter, label)
            x += bar_width + bar_gap


class SnoozeIndicatorCard(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName('chartCard')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel('Snooze Pressure')
        title.setObjectName('chartTitle')

        self.value = QLabel('0')
        self.value.setObjectName('snoozeValue')
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bar = QProgressBar()
        self.bar.setRange(0, 20)
        self.bar.setValue(0)
        self.bar.setFormat('%v')

        layout.addWidget(title)
        layout.addWidget(self.value)
        layout.addWidget(self.bar)

    def set_value(self, snooze_total: int) -> None:
        cap = max(20, snooze_total)
        self.bar.setRange(0, cap)
        self.bar.setValue(snooze_total)
        self.value.setText(str(snooze_total))
