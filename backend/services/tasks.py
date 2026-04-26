from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional

from backend.db import Database
from backend.models import MissionCreate, MissionPatch, MissionUpdate


class TaskService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def fetch_tasks(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, title, priority, mode, status, reminder_at, next_check_at,
                   last_progress_at, snooze_count, created_at, completed_at
            FROM tasks
            ORDER BY created_at DESC
        """
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            tasks = cursor.fetchall()
            cursor.close()

        task_ids = [task["id"] for task in tasks]
        micro_map: dict[int, list[dict[str, Any]]] = {task_id: [] for task_id in task_ids}
        if task_ids:
            in_clause = ",".join(["%s"] * len(task_ids))
            micro_query = f"""
                SELECT id, task_id, title, completed, completed_at, sort_order
                FROM micro_actions
                WHERE task_id IN ({in_clause})
                ORDER BY task_id, sort_order, id
            """
            with self.db.connect() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(micro_query, tuple(task_ids))
                for row in cursor.fetchall():
                    row["completed"] = bool(row["completed"])
                    micro_map[row["task_id"]].append(row)
                cursor.close()

        for task in tasks:
            task["micro_actions"] = micro_map.get(task["id"], [])
        return tasks

    def get_task(self, task_id: int) -> Optional[dict[str, Any]]:
        for task in self.fetch_tasks():
            if int(task["id"]) == task_id:
                return task
        return None

    def add_task(self, payload: MissionCreate) -> int:
        query = """
            INSERT INTO tasks (title, priority, mode, reminder_at)
            VALUES (%s, %s, %s, %s)
        """
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                (payload.title.strip(), payload.priority.value, payload.mode.value, payload.reminder_at),
            )
            task_id = cursor.lastrowid
            cursor.close()
        return int(task_id)

    def update_task(self, task_id: int, payload: MissionUpdate) -> None:
        query = """
            UPDATE tasks
            SET title = %s, priority = %s, mode = %s, reminder_at = %s
            WHERE id = %s
        """
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                (
                    payload.title.strip(),
                    payload.priority.value,
                    payload.mode.value,
                    payload.reminder_at,
                    task_id,
                ),
            )
            cursor.close()

    def patch_task(self, task_id: int, payload: MissionPatch) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if payload.title is not None:
            updates.append("title = %s")
            params.append(payload.title.strip())
        if payload.priority is not None:
            updates.append("priority = %s")
            params.append(payload.priority.value)
        if payload.mode is not None:
            updates.append("mode = %s")
            params.append(payload.mode.value)
        if payload.status is not None:
            updates.append("status = %s")
            params.append(payload.status.value)
            if payload.status.value == "COMPLETED":
                updates.append("completed_at = COALESCE(completed_at, NOW())")
                updates.append("last_progress_at = NOW()")
            elif payload.status.value != "COMPLETED":
                updates.append("completed_at = NULL")
        if payload.clear_reminder:
            updates.append("reminder_at = NULL")
        elif payload.reminder_at is not None:
            updates.append("reminder_at = %s")
            params.append(payload.reminder_at)
        if not updates:
            return

        params.append(task_id)
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s", tuple(params))
            cursor.close()

    def delete_task(self, task_id: int) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            cursor.close()

    def set_task_completed(self, task_id: int, completed: bool) -> None:
        if completed:
            query = """
                UPDATE tasks
                SET status = 'COMPLETED', completed_at = NOW(), last_progress_at = NOW()
                WHERE id = %s
            """
        else:
            query = "UPDATE tasks SET status = 'PENDING', completed_at = NULL WHERE id = %s"
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, (task_id,))
            cursor.close()

    def start_task(self, task_id: int) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE tasks
                SET status = 'ACTIVE',
                    last_progress_at = NOW(),
                    next_check_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                WHERE id = %s
                """,
                (task_id,),
            )
            cursor.close()

    def get_steps(self, task_id: int) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, task_id, title, completed, completed_at, sort_order
                FROM micro_actions
                WHERE task_id = %s
                ORDER BY sort_order, id
                """,
                (task_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
        for row in rows:
            row["completed"] = bool(row["completed"])
        return rows

    def add_step(self, task_id: int, title: str) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM micro_actions WHERE task_id = %s",
                (task_id,),
            )
            next_sort = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO micro_actions (task_id, title, sort_order) VALUES (%s, %s, %s)",
                (task_id, title.strip(), next_sort),
            )
            step_id = cursor.lastrowid
            cursor.close()
        return int(step_id)

    def update_step(self, step_id: int, title: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE micro_actions SET title = %s WHERE id = %s", (title.strip(), step_id))
            cursor.close()

    def delete_step(self, step_id: int) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM micro_actions WHERE id = %s", (step_id,))
            cursor.close()

    def set_step_completed(self, step_id: int, completed: bool) -> Optional[int]:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT task_id FROM micro_actions WHERE id = %s", (step_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                return None
            task_id = int(row[0])
            if completed:
                cursor.execute(
                    "UPDATE micro_actions SET completed = TRUE, completed_at = NOW() WHERE id = %s",
                    (step_id,),
                )
                cursor.execute("UPDATE tasks SET last_progress_at = NOW() WHERE id = %s", (task_id,))
            else:
                cursor.execute(
                    "UPDATE micro_actions SET completed = FALSE, completed_at = NULL WHERE id = %s",
                    (step_id,),
                )
            cursor.close()
        return task_id

    def get_totals(self) -> dict[str, int]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed
                FROM tasks
                """
            )
            row = cursor.fetchone()
            cursor.close()
        return {"total": int(row["total"] or 0), "completed": int(row["completed"] or 0)}

    def get_dashboard_stats(self) -> dict[str, int]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_tasks,
                    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) AS pending_tasks,
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_tasks,
                    SUM(CASE WHEN status = 'AWAY' THEN 1 ELSE 0 END) AS away_tasks,
                    SUM(CASE WHEN snooze_count > 0 AND status <> 'COMPLETED' THEN 1 ELSE 0 END) AS snoozed_tasks
                FROM tasks
                """
            )
            row = cursor.fetchone()
            cursor.close()
        return {key: int(row[key] or 0) for key in row}

    def get_today_execution_score(self) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN completed_at IS NOT NULL AND DATE(completed_at) = CURDATE()
                           THEN 1 ELSE 0 END) AS completed_today
                FROM tasks
                """
            )
            row = cursor.fetchone()
            cursor.close()
        total = int(row["total"] or 0)
        if total == 0:
            return 0
        return int((int(row["completed_today"] or 0) / total) * 100)

    def get_timeline(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, title, status, priority, reminder_at, next_check_at, created_at
                FROM tasks
                ORDER BY
                    CASE status
                        WHEN 'ACTIVE' THEN 1
                        WHEN 'PENDING' THEN 2
                        WHEN 'AWAY' THEN 3
                        WHEN 'COMPLETED' THEN 4
                        ELSE 5
                    END,
                    COALESCE(next_check_at, reminder_at, created_at) ASC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows

    def get_daily_completion_counts(self, days: int = 7) -> list[dict[str, int | str]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT DATE(completed_at) AS day, COUNT(*) AS completed_count
                FROM tasks
                WHERE completed_at IS NOT NULL
                  AND DATE(completed_at) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(completed_at)
                ORDER BY day ASC
                """,
                (days - 1,),
            )
            rows = cursor.fetchall()
            cursor.close()
        row_map = {str(row["day"]): int(row["completed_count"] or 0) for row in rows}
        today = date.today()
        return [
            {"label": (today - timedelta(days=(days - 1 - offset))).strftime("%a"),
             "value": row_map.get((today - timedelta(days=(days - 1 - offset))).isoformat(), 0)}
            for offset in range(days)
        ]

    def get_next_attention_task(self) -> Optional[dict[str, Any]]:
        query = """
            SELECT id, title, priority, mode, status, reminder_at, next_check_at,
                   last_progress_at, snooze_count
            FROM tasks
            WHERE status <> 'COMPLETED'
              AND (
                    (status = 'PENDING' AND reminder_at IS NOT NULL AND reminder_at <= NOW())
                 OR (status = 'ACTIVE' AND next_check_at IS NOT NULL AND next_check_at <= NOW()
                     AND (last_progress_at IS NULL OR TIMESTAMPDIFF(MINUTE, last_progress_at, NOW()) >= 15))
                 OR (status = 'AWAY' AND next_check_at IS NOT NULL AND next_check_at <= NOW())
              )
            ORDER BY COALESCE(next_check_at, reminder_at, NOW()) ASC, created_at ASC
            LIMIT 1
        """
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
        return row

    def get_due_reminders(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, title, priority, mode, status, reminder_at, next_check_at,
                   last_progress_at, snooze_count, created_at, completed_at
            FROM tasks
            WHERE status <> 'COMPLETED'
              AND reminder_at IS NOT NULL
              AND reminder_at <= NOW()
            ORDER BY reminder_at ASC, created_at ASC
        """
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

        for row in rows:
            row["micro_actions"] = []
        return rows

    def snooze_task(self, task_id: int, minutes: int = 5) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE tasks
                SET snooze_count = snooze_count + 1,
                    reminder_at = DATE_ADD(NOW(), INTERVAL %s MINUTE),
                    next_check_at = NULL,
                    status = 'PENDING'
                WHERE id = %s
                """,
                (minutes, task_id),
            )
            cursor.close()

    def apply_alert_action(self, task_id: int, action: str) -> None:
        actions = {
            "start": """
                UPDATE tasks SET status = 'ACTIVE', last_progress_at = NOW(),
                    next_check_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE id = %s
            """,
            "snooze_5": """
                UPDATE tasks SET snooze_count = snooze_count + 1,
                    reminder_at = DATE_ADD(NOW(), INTERVAL 5 MINUTE),
                    next_check_at = NULL, status = 'PENDING' WHERE id = %s
            """,
            "snooze_15": """
                UPDATE tasks SET snooze_count = snooze_count + 1,
                    reminder_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE),
                    next_check_at = NULL, status = 'PENDING' WHERE id = %s
            """,
            "away": """
                UPDATE tasks SET status = 'AWAY',
                    next_check_at = DATE_ADD(NOW(), INTERVAL 45 MINUTE) WHERE id = %s
            """,
            "done": """
                UPDATE tasks SET status = 'COMPLETED', completed_at = NOW(),
                    last_progress_at = NOW() WHERE id = %s
            """,
        }
        if action not in actions:
            raise ValueError(f"Unknown action: {action}")
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(actions[action], (task_id,))
            cursor.close()
