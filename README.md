# Red Roadmap

A desktop mission/task manager built to help you start work and keep momentum.

`Red Roadmap` is a local-first Python app with a PySide6 UI and MySQL storage. It supports tasks, micro-actions, reminders, and fullscreen attention alerts when it is time to act.

## Highlights

- Desktop app (Python + PySide6)
- MySQL-backed task and micro-action storage
- Basic mission dashboard with live status counts
- Add, edit, complete, and delete missions
- Add/edit/delete/check micro-actions
- Fullscreen red alert with audio loop
- Snooze, away mode, start now, and mark complete actions
- Reminder engine checks every 10 seconds
- Local-only, no cloud services required

## Current UI

- Header: app title, subtitle, date/time, execution score
- Progress card: completed/total + progress bar
- Status strip: active, pending, completed, away, snoozed
- Mission list: large scroll area with mission cards
- Timeline panel: quick left-side roadmap list

## Reminder behavior

A mission needs attention if any condition is true:

1. `status = PENDING` and `reminder_at <= NOW()`
2. `status = ACTIVE` and `next_check_at <= NOW()` and no recent progress
3. `status = AWAY` and `next_check_at <= NOW()`

When attention is needed, the app opens a fullscreen alert with controls:

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
  icon.ico
  ui/
    main_window.py
    task_card.py
    alert_window.py
```

## Requirements

- Python 3.10+
- MySQL Server 8+
- Windows/macOS/Linux (Windows is the primary tested target)

## Quick start

### 1) Create virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r red_roadmap/requirements.txt
```

### 3) Create database

```sql
CREATE DATABASE red_roadmap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4) Apply schema and seed data

```bash
mysql -u root -p red_roadmap < red_roadmap/schema.sql
```

### 5) Configure environment variables

Copy `red_roadmap/.env.example` to `red_roadmap/.env` and set:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

### 6) Run app

```bash
cd red_roadmap
python app.py
```

## Build Windows executable

From repo root:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile --name RedRoadmap --icon red_roadmap/icon.ico --paths red_roadmap --add-data "red_roadmap/.env;." red_roadmap/app.py
```

Output:

- `dist/RedRoadmap.exe`

## Desktop shortcut (Windows)

1. Right-click `dist/RedRoadmap.exe`
2. Select `Send to > Desktop (create shortcut)`
3. Open shortcut `Properties`
4. Set `Start in` to your `dist` folder path

## GitHub Actions (Windows build)

This repo includes:

- `.github/workflows/build-windows.yml`

It builds a Windows EXE and uploads it as a workflow artifact.

Required GitHub secrets:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

## Troubleshooting

- `Could not connect to MySQL`: verify `.env` values and ensure MySQL is running.
- No alert appears: confirm a task has a due `reminder_at` or due `next_check_at`.
- No audio: on non-Windows systems it falls back to app beep.
- Scroll feels limited: increase app window height and ensure mission list has focus.

## License

This project was created for academic purposes and does not currently use an open-source license.

## Screenshots

### Alarm Reminder

![Main Dashboard](screenshots/Screenshot%202026-04-25%20215100.png)

### Roadmap View

![Roadmap View](screenshots/Screenshot%202026-04-25%20215042.png)
