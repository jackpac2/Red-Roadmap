# Red Roadmap

Red Roadmap is a local-first mission/task manager with MySQL storage. The original PySide6 desktop app is still available, and the repo now also contains the migration path to a modern Electron desktop app with a FastAPI backend and React/Tailwind frontend.

## Architecture

- `red_roadmap/` contains the existing PySide6 app and remains runnable.
- `backend/` contains the FastAPI API, MySQL database adapter, Pydantic models, and task/reminder services.
- `frontend/` contains the Vite + React + Tailwind dashboard UI.
- `desktop/` contains the Electron main process that starts the Python backend and opens the React UI.

The database schema is still `red_roadmap/schema.sql`; no migration is required for this first pass.

## Requirements

- Python 3.10+
- MySQL Server 8+
- Node.js 20+
- Windows for the packaged `.exe` flow

## Database Setup

```sql
CREATE DATABASE red_roadmap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```powershell
mysql -u root -p red_roadmap < red_roadmap/schema.sql
```

Copy `red_roadmap/.env.example` to `red_roadmap/.env` and set:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=red_roadmap
```

Do not commit `.env` files.

## Run The Legacy PySide App

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r red_roadmap/requirements.txt
cd red_roadmap
python app.py
```

## Run The FastAPI Backend

From the repo root:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

API health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Run The React Frontend

```powershell
npm install
npm run dev --workspace frontend
```

Open `http://127.0.0.1:5173`. The frontend calls the FastAPI backend at `http://127.0.0.1:8000` by default. Override with `VITE_API_BASE_URL` if needed.

## Run The Electron App In Development

```powershell
npm install
npm run dev
```

Electron starts the FastAPI backend silently, waits for `/health`, and opens the Vite UI.

## Build The New Windows App

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
pip install pyinstaller
npm install
npm run build
```

Build output is written to `release/`.

## Legacy PyInstaller Build

The old PySide-only build is still possible while the Electron app is being verified:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile --name RedRoadmap --icon red_roadmap/icon.ico --paths red_roadmap --add-data "red_roadmap/.env;." red_roadmap/app.py
```

## API Surface

The FastAPI backend exposes:

- `GET /api/missions`
- `POST /api/missions`
- `PUT /api/missions/{task_id}`
- `PATCH /api/missions/{task_id}`
- `DELETE /api/missions/{task_id}`
- `POST /api/missions/{task_id}/complete`
- `POST /api/missions/{task_id}/start`
- `GET /api/missions/{task_id}/steps`
- `POST /api/missions/{task_id}/steps`
- `PUT /api/steps/{step_id}`
- `DELETE /api/steps/{step_id}`
- `POST /api/steps/{step_id}/complete`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/progress`
- `GET /api/dashboard/execution-score`
- `GET /api/roadmap/timeline`
- `GET /api/reminders/next-attention`
- `POST /api/missions/{task_id}/alert-action`

## Notes

<<<<<<< HEAD
- The PySide app has not been deleted or rewired.
- The new backend reads `backend/.env`, `red_roadmap/.env`, or root `.env`, in that order.
- The Electron alert/audio experience is not yet a fullscreen replacement for the old PySide alert window; the backend exposes the reminder action endpoints needed to build that UI next.
=======
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
