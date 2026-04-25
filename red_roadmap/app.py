import sys

from mysql.connector import Error
from PySide6.QtWidgets import QApplication, QMessageBox

from db import DatabaseConfigError, get_db
from models import TaskRepository
from reminder_engine import ReminderEngine
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    try:
        db = get_db()
        db.test_connection()
    except DatabaseConfigError as exc:
        QMessageBox.critical(None, 'Configuration Error', str(exc))
        return 1
    except Error as exc:
        QMessageBox.critical(
            None,
            'Database Connection Error',
            f'Could not connect to MySQL. Check red_roadmap/.env settings.\n\n{exc}',
        )
        return 1

    repo = TaskRepository(db)
    reminder_engine = ReminderEngine(repo)

    window = MainWindow(repo, reminder_engine)
    window.show()
    reminder_engine.start()

    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
