from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from mysql.connector import Error

from db import Database


@dataclass
class Task:
    id: int
    title: str
    priority: str
    mode: str
    status: str
    reminder_at: Optional[datetime]
    next_check_at: Optional[datetime]
    last_progress_at: Optional[datetime]
    snooze_count: int
    created_at: datetime
    completed_at: Optional[datetime]


class TaskRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def fetch_tasks(self) -> List[Dict[str, Any]]:
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

        task_ids = [task['id'] for task in tasks]
        micro_map: Dict[int, List[Dict[str, Any]]] = {task_id: [] for task_id in task_ids}

        if task_ids:
            in_clause = ','.join(['%s'] * len(task_ids))
            micro_query = f"""
                SELECT id, task_id, title, completed, completed_at, sort_order
                FROM micro_actions
                WHERE task_id IN ({in_clause})
                ORDER BY task_id, sort_order, id
            """
            with self.db.connect() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(micro_query, tuple(task_ids))
                micro_rows = cursor.fetchall()
                cursor.close()

            for row in micro_rows:
                micro_map[row['task_id']].append(row)

        for task in tasks:
            task['micro_actions'] = micro_map.get(task['id'], [])

        return tasks

    def add_task(
        self,
        title: str,
        priority: str = 'MEDIUM',
        mode: str = 'FLEXIBLE',
        reminder_at: Optional[datetime] = None,
    ) -> int:
        query = """
            INSERT INTO tasks (title, priority, mode, reminder_at)
            VALUES (%s, %s, %s, %s)
        """
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, (title, priority, mode, reminder_at))
            task_id = cursor.lastrowid
            cursor.close()
        return int(task_id)

    def update_task(
        self,
        task_id: int,
        title: str,
        priority: str,
        mode: str,
        reminder_at: Optional[datetime],
    ) -> None:
        query = """
            UPDATE tasks
            SET title = %s,
                priority = %s,
                mode = %s,
                reminder_at = %s
            WHERE id = %s
        """
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, (title, priority, mode, reminder_at, task_id))
            cursor.close()

    def add_micro_action(self, task_id: int, title: str) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                'SELECT COALESCE(MAX(sort_order), -1) + 1 FROM micro_actions WHERE task_id = %s',
                (task_id,),
            )
            next_sort = cursor.fetchone()[0]
            cursor.execute(
                'INSERT INTO micro_actions (task_id, title, sort_order) VALUES (%s, %s, %s)',
                (task_id, title, next_sort),
            )
            micro_id = cursor.lastrowid
            cursor.close()
        return int(micro_id)

    def update_micro_action_title(self, micro_id: int, title: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                'UPDATE micro_actions SET title = %s WHERE id = %s',
                (title, micro_id),
            )
            cursor.close()

    def delete_micro_action(self, micro_id: int) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM micro_actions WHERE id = %s', (micro_id,))
            cursor.close()

    def set_task_completed(self, task_id: int, completed: bool) -> None:
        if completed:
            query = """
                UPDATE tasks
                SET status = 'COMPLETED', completed_at = NOW(), last_progress_at = NOW()
                WHERE id = %s
            """
        else:
            query = """
                UPDATE tasks
                SET status = 'PENDING', completed_at = NULL
                WHERE id = %s
            """

        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, (task_id,))
            cursor.close()

    def set_micro_completed(self, micro_id: int, completed: bool) -> Optional[int]:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT task_id FROM micro_actions WHERE id = %s', (micro_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                return None

            task_id = int(row[0])
            if completed:
                cursor.execute(
                    """
                    UPDATE micro_actions
                    SET completed = TRUE, completed_at = NOW()
                    WHERE id = %s
                    """,
                    (micro_id,),
                )
                cursor.execute(
                    'UPDATE tasks SET last_progress_at = NOW() WHERE id = %s',
                    (task_id,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE micro_actions
                    SET completed = FALSE, completed_at = NULL
                    WHERE id = %s
                    """,
                    (micro_id,),
                )
            cursor.close()
        return task_id

    def all_micro_complete(self, task_id: int) -> bool:
        query = """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN completed = TRUE THEN 1 ELSE 0 END) AS done_count
            FROM micro_actions
            WHERE task_id = %s
        """
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (task_id,))
            row = cursor.fetchone()
            cursor.close()

        if not row or row['total'] == 0:
            return False
        return int(row['total']) == int(row['done_count'] or 0)

    def delete_all_tasks(self) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM tasks')
            cursor.close()

    def delete_task(self, task_id: int) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
            cursor.close()

    def start_task(self, task_id: int) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE tasks
                SET status = 'ACTIVE',
                    last_progress_at = NOW(),
                    reminder_at = NULL,
                    next_check_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                WHERE id = %s
                """,
                (task_id,),
            )
            cursor.close()

    def add_tasks_from_lines(self, lines: List[str]) -> int:
        cleaned = [line.strip() for line in lines if line.strip()]
        if not cleaned:
            return 0

        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.executemany(
                'INSERT INTO tasks (title, priority, mode) VALUES (%s, %s, %s)',
                [(line, 'MEDIUM', 'FLEXIBLE') for line in cleaned],
            )
            inserted = cursor.rowcount
            cursor.close()
        return int(inserted)

    def get_next_attention_task(self) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id, title, priority, mode, status, reminder_at, next_check_at,
                   last_progress_at, snooze_count
            FROM tasks
            WHERE status <> 'COMPLETED'
              AND (
                    (status = 'PENDING' AND reminder_at IS NOT NULL AND reminder_at <= NOW())
                 OR (status = 'ACTIVE' AND next_check_at IS NOT NULL AND next_check_at <= NOW()
                     AND (last_progress_at IS NULL OR TIMESTAMPDIFF(MINUTE, last_progress_at, NOW()) >= 15))
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

    def apply_alert_action(self, task_id: int, action: str) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()

            if action == 'start':
                cursor.execute(
                    """
                    UPDATE tasks
                    SET status = 'ACTIVE',
                        last_progress_at = NOW(),
                        reminder_at = NULL,
                        next_check_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                    WHERE id = %s
                    """,
                    (task_id,),
                )
            elif action == 'snooze_5':
                cursor.execute(
                    """
                    UPDATE tasks
                    SET snooze_count = snooze_count + 1,
                        reminder_at = DATE_ADD(NOW(), INTERVAL 10 MINUTE),
                        next_check_at = NULL,
                        status = 'PENDING'
                    WHERE id = %s
                    """,
                    (task_id,),
                )
            elif action == 'snooze_15':
                cursor.execute(
                    """
                    UPDATE tasks
                    SET snooze_count = snooze_count + 1,
                        reminder_at = DATE_ADD(NOW(), INTERVAL 10 MINUTE),
                        next_check_at = NULL,
                        status = 'PENDING'
                    WHERE id = %s
                    """,
                    (task_id,),
                )
            elif action == 'away':
                cursor.execute(
                    """
                    UPDATE tasks
                    SET status = 'AWAY',
                        reminder_at = NULL,
                        next_check_at = DATE_ADD(NOW(), INTERVAL 45 MINUTE)
                    WHERE id = %s
                    """,
                    (task_id,),
                )
            elif action == 'done':
                cursor.execute(
                    """
                    UPDATE tasks
                    SET status = 'COMPLETED',
                        completed_at = NOW(),
                        last_progress_at = NOW()
                    WHERE id = %s
                    """,
                    (task_id,),
                )
            else:
                raise ValueError(f'Unknown action: {action}')

            cursor.close()

    def get_totals(self) -> Dict[str, int]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed
                FROM tasks
                """
            )
            row = cursor.fetchone()
            cursor.close()

        return {
            'total': int(row['total'] or 0),
            'completed': int(row['completed'] or 0),
        }

    def get_dashboard_stats(self) -> Dict[str, int]:
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

        return {
            'active_tasks': int(row['active_tasks'] or 0),
            'pending_tasks': int(row['pending_tasks'] or 0),
            'completed_tasks': int(row['completed_tasks'] or 0),
            'away_tasks': int(row['away_tasks'] or 0),
            'snoozed_tasks': int(row['snoozed_tasks'] or 0),
        }

    def get_priority_breakdown(self) -> Dict[str, int]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT priority, COUNT(*) AS count
                FROM tasks
                GROUP BY priority
                """
            )
            rows = cursor.fetchall()
            cursor.close()

        output = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        for row in rows:
            output[str(row['priority'])] = int(row['count'] or 0)
        return output

    def get_status_breakdown(self) -> Dict[str, int]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM tasks
                GROUP BY status
                """
            )
            rows = cursor.fetchall()
            cursor.close()

        output = {'PENDING': 0, 'ACTIVE': 0, 'AWAY': 0, 'COMPLETED': 0}
        for row in rows:
            output[str(row['status'])] = int(row['count'] or 0)
        return output

    def get_daily_completion_counts(self, days: int = 7) -> List[Dict[str, int | str]]:
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

        row_map = {str(row['day']): int(row['completed_count'] or 0) for row in rows}
        today = date.today()
        series: List[Dict[str, int | str]] = []
        for offset in range(days):
            d = today - timedelta(days=(days - 1 - offset))
            key = d.isoformat()
            series.append({'label': d.strftime('%a'), 'value': row_map.get(key, 0)})
        return series

    def get_current_streak(self) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT DISTINCT DATE(completed_at) AS completed_day
                FROM tasks
                WHERE completed_at IS NOT NULL
                ORDER BY completed_day DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()

        completed_days = {row[0] for row in rows if row and row[0] is not None}
        today = date.today()
        streak = 0
        probe = today
        while probe in completed_days:
            streak += 1
            probe = probe - timedelta(days=1)
        return streak

    def get_total_completed_micro_actions(self) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT COUNT(*) FROM micro_actions WHERE completed = TRUE')
            value = cursor.fetchone()[0]
            cursor.close()
        return int(value or 0)

    def get_today_execution_score(self) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN completed_at IS NOT NULL AND DATE(completed_at) = CURDATE() THEN 1 ELSE 0 END) AS completed_today
                FROM tasks
                """
            )
            row = cursor.fetchone()
            cursor.close()

        total = int(row['total'] or 0)
        completed_today = int(row['completed_today'] or 0)
        if total == 0:
            return 0
        return int((completed_today / total) * 100)

    def get_snooze_indicator_value(self) -> int:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT COALESCE(SUM(snooze_count), 0) FROM tasks WHERE status <> \'COMPLETED\'')
            value = cursor.fetchone()[0]
            cursor.close()
        return int(value or 0)

    def get_active_mission(self) -> Optional[Dict[str, Any]]:
        attention = self.get_next_attention_task()
        if attention:
            return attention

        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, title, priority, mode, status, reminder_at, next_check_at, last_progress_at, snooze_count
                FROM tasks
                WHERE status <> 'COMPLETED'
                ORDER BY
                    CASE status
                        WHEN 'ACTIVE' THEN 1
                        WHEN 'PENDING' THEN 2
                        WHEN 'AWAY' THEN 3
                        ELSE 4
                    END,
                    COALESCE(next_check_at, reminder_at, created_at) ASC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            cursor.close()
        return row
