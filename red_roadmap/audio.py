from __future__ import annotations

import platform
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

try:
    import winsound
except Exception:  # pragma: no cover
    winsound = None


class AnnoyingAudioPlayer(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start_loop(self, intensity: int = 1) -> None:
        self.stop()
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_loop,
            args=(max(1, intensity),),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        self._thread = None

    def _run_loop(self, intensity: int) -> None:
        is_windows = platform.system().lower().startswith('win') and winsound is not None
        delay = 0.8

        while not self._stop_event.is_set():
            if is_windows:
                try:
                    winsound.Beep(1000, 450)
                except Exception:
                    self._beep_fallback()
            else:
                self._beep_fallback()

            time.sleep(delay)

    @staticmethod
    def _beep_fallback() -> None:
        app = QApplication.instance()
        if app:
            app.beep()
