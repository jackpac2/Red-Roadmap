# Red Roadmap (Version 1)

Red Roadmap is a local Python desktop mission-control task manager built to push fast execution.
It uses PySide6 for desktop UI, MySQL for storage, and a fullscreen red alert with looping audio for reminders.

## What is implemented

- Mission control UI style (dark futuristic dashboard with neon accents).
- Header with:
  - `RED ROADMAP`
  - `SYSTEM ONLINE`
  - live clock
  - mission progress percentage
- Dashboard metrics:
  - Total Tasks
  - Completed Tasks
  - Active Tasks
  - Snoozed Tasks
  - Away From PC Tasks
  - Completion Rate
  - Current Streak
  - Total Micro-Actions Completed
- Chart widgets:
  - overall completion progress bar
  - daily completion mini bar chart
  - priority breakdown bars
  - task status breakdown bars
  - snooze pressure indicator
- Dashboard counters:
  - Active Mission
  - Pending Tasks
  - Completed Tasks
  - Snoozed Tasks
  - Away From PC Tasks
- Timeline panel and mission task cards.
- Task card badges:
  - PRIORITY
  - MODE
  - STATUS
- Task card actions:
  - Start
  - Expand Steps
  - Delete
  - Complete
- Global actions:
  - Add Mission
  - Paste Missions
  - Focus Mode
  - Select Multiple
  - Delete All

## Micro-actions UX improvements

- Expanded task cards stay expanded after refresh.
- Expanded state is tracked in memory with `expanded_task_ids`.
- Add micro-action input clears after submit.
- Pressing `Enter` in micro-action input adds the step.
- Focus returns to the micro-action input after adding a step.
- Micro-action row includes:
  - checkbox
  - title
  - edit button
  - delete button
- Completing a micro-action updates:
  - `micro_actions.completed`
  - `micro_actions.completed_at`
  - parent `tasks.last_progress_at`
- If all micro-actions are complete, app asks:
  - `All micro-actions are complete. Mark the whole task as done?`

## Deletion behavior

- `Delete All` removes all tasks and micro-actions.
- Per-task `Delete` button removes only that task (and its micro-actions via FK cascade).
- Per-task delete confirmation:
  - `Delete this task and all its micro-actions?`
- Micro-action delete removes only that micro-action.

## Fullscreen alert

Reminder behavior is unchanged (10-second checks, same DB state rules).
Alert UI now uses mission wording and includes:

- `MISSION ATTENTION REQUIRED`
- task title
- snooze status panel
- buttons:
  - `START NOW`
  - `SNOOZE 5`
  - `SNOOZE 15`
  - `AWAY FROM PC`
  - `MARK COMPLETE`

## Project structure

```text
red_roadmap/
  app.py
  db.py
  models.py
  reminder_engine.py
  audio.py
  schema.sql
  requirements.txt
  .env.example
  ui/
    dashboard_widgets.py
    main_window.py
    alert_window.py
    task_card.py
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```bash
pip install -r red_roadmap/requirements.txt
```

3. Create the MySQL database.

```sql
CREATE DATABASE red_roadmap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

4. Apply schema and seed data.

```bash
mysql -u root -p red_roadmap < red_roadmap/schema.sql
```

5. Configure environment variables.

- Copy `red_roadmap/.env.example` to `red_roadmap/.env`
- Set:
  - `DB_HOST`
  - `DB_PORT`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_NAME`

6. Run the app.

```bash
cd red_roadmap
python app.py
```

## Reminder logic

A task needs attention when any condition is true:

1. `status = PENDING` and `reminder_at <= NOW()`
2. `status = ACTIVE` and `next_check_at <= NOW()` and no recent progress
3. `status = AWAY` and `next_check_at <= NOW()`

## PyInstaller packaging

```bash
pip install pyinstaller
pyinstaller --name "RedRoadmap" --windowed --onefile red_roadmap/app.py
```

If you need to bundle additional files:

```bash
pyinstaller --name "RedRoadmap" --windowed --onefile \
  --add-data "red_roadmap/.env.example;." \
  red_roadmap/app.py
```

## Notes

- Local-only app, no cloud services.
- Audio uses `winsound` on Windows when available; fallback is app beep.
- Prioritizes working behavior over advanced polish.
