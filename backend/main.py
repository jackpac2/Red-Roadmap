from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mysql.connector import Error as MySQLError

from backend.db import DatabaseConfigError, get_db
from backend.models import (
    AlertActionRequest,
    CompleteRequest,
    DashboardStats,
    ExecutionScore,
    Mission,
    MissionCreate,
    MissionPatch,
    MissionUpdate,
    ProgressSummary,
    ReminderUpdate,
    SnoozeRequest,
    Step,
    StepCreate,
    StepUpdate,
    TimelineItem,
)
from backend.services.reminders import ReminderService
from backend.services.tasks import TaskService

app = FastAPI(title="Red Roadmap API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_task_service() -> TaskService:
    try:
        return TaskService(get_db())
    except DatabaseConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_reminder_service(service: TaskService = Depends(get_task_service)) -> ReminderService:
    return ReminderService(service)


@app.exception_handler(MySQLError)
async def mysql_exception_handler(_request, exc: MySQLError):
    return JSONResponse(status_code=500, content={"detail": f"Database error: {exc}"})


@app.get("/health")
def health(service: TaskService = Depends(get_task_service)) -> dict[str, str]:
    service.db.test_connection()
    return {"status": "ok"}


@app.get("/api/missions", response_model=list[Mission])
def get_missions(service: TaskService = Depends(get_task_service)):
    return service.fetch_tasks()


@app.post("/api/missions", response_model=Mission, status_code=201)
def create_mission(payload: MissionCreate, service: TaskService = Depends(get_task_service)):
    task_id = service.add_task(payload)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=500, detail="Mission was created but could not be loaded.")
    return task


@app.put("/api/missions/{task_id}", response_model=Mission)
def edit_mission(task_id: int, payload: MissionUpdate, service: TaskService = Depends(get_task_service)):
    service.update_task(task_id, payload)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


@app.patch("/api/missions/{task_id}", response_model=Mission)
def patch_mission(task_id: int, payload: MissionPatch, service: TaskService = Depends(get_task_service)):
    service.patch_task(task_id, payload)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


@app.put("/api/missions/{task_id}/reminder", response_model=Mission)
def set_mission_reminder(task_id: int, payload: ReminderUpdate, service: TaskService = Depends(get_task_service)):
    service.set_task_reminder(task_id, payload.reminder_at)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


@app.delete("/api/missions/{task_id}/reminder", response_model=Mission)
def clear_mission_reminder(task_id: int, service: TaskService = Depends(get_task_service)):
    service.clear_task_reminder(task_id)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


@app.delete("/api/missions/{task_id}", status_code=204)
def delete_mission(task_id: int, service: TaskService = Depends(get_task_service)):
    service.delete_task(task_id)
    return None


@app.delete("/api/missions", status_code=204)
def delete_all_missions(service: TaskService = Depends(get_task_service)):
    service.delete_all_tasks()
    return None


@app.post("/api/missions/{task_id}/complete", response_model=Mission)
def complete_mission(task_id: int, payload: CompleteRequest, service: TaskService = Depends(get_task_service)):
    service.set_task_completed(task_id, payload.completed)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


@app.post("/api/missions/{task_id}/start", response_model=Mission)
def start_mission(task_id: int, service: TaskService = Depends(get_task_service)):
    service.start_task(task_id)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


@app.get("/api/missions/{task_id}/steps", response_model=list[Step])
def get_steps(task_id: int, service: TaskService = Depends(get_task_service)):
    return service.get_steps(task_id)


@app.post("/api/missions/{task_id}/steps", response_model=Step, status_code=201)
def add_step(task_id: int, payload: StepCreate, service: TaskService = Depends(get_task_service)):
    step_id = service.add_step(task_id, payload.title)
    steps = service.get_steps(task_id)
    return next(step for step in steps if int(step["id"]) == step_id)


@app.put("/api/steps/{step_id}", status_code=204)
def edit_step(step_id: int, payload: StepUpdate, service: TaskService = Depends(get_task_service)):
    service.update_step(step_id, payload.title)
    return None


@app.delete("/api/steps/{step_id}", status_code=204)
def delete_step(step_id: int, service: TaskService = Depends(get_task_service)):
    service.delete_step(step_id)
    return None


@app.post("/api/steps/{step_id}/complete", status_code=204)
def complete_step(step_id: int, payload: CompleteRequest, service: TaskService = Depends(get_task_service)):
    task_id = service.set_step_completed(step_id, payload.completed)
    if task_id is None:
        raise HTTPException(status_code=404, detail="Step not found.")
    return None


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(service: TaskService = Depends(get_task_service)):
    return service.get_dashboard_stats()


@app.get("/api/dashboard/progress", response_model=ProgressSummary)
def progress(service: TaskService = Depends(get_task_service)):
    totals = service.get_totals()
    total = totals["total"]
    completed = totals["completed"]
    return {**totals, "percent": int((completed / total) * 100) if total else 0}


@app.get("/api/dashboard/execution-score", response_model=ExecutionScore)
def execution_score(service: TaskService = Depends(get_task_service)):
    return {"score": service.get_today_execution_score()}


@app.get("/api/dashboard/daily-completions")
def daily_completions(days: int = 7, service: TaskService = Depends(get_task_service)):
    return service.get_daily_completion_counts(days)


@app.get("/api/roadmap/timeline", response_model=list[TimelineItem])
def timeline(service: TaskService = Depends(get_task_service)):
    return service.get_timeline()


@app.get("/api/reminders/next-attention")
def next_attention(reminders: ReminderService = Depends(get_reminder_service)):
    return reminders.get_next_attention_task()


@app.get("/api/reminders/due", response_model=list[Mission])
def due_reminders(reminders: ReminderService = Depends(get_reminder_service)):
    next_due = reminders.get_next_attention_task()
    return [next_due] if next_due else []


@app.post("/api/missions/{task_id}/snooze", response_model=Mission)
def snooze_mission(
    task_id: int,
    payload: SnoozeRequest,
    reminders: ReminderService = Depends(get_reminder_service),
    service: TaskService = Depends(get_task_service),
):
    reminders.snooze(task_id, payload.minutes)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


@app.post("/api/missions/{task_id}/alert-action", response_model=Mission)
def alert_action(
    task_id: int,
    payload: AlertActionRequest,
    reminders: ReminderService = Depends(get_reminder_service),
    service: TaskService = Depends(get_task_service),
):
    reminders.apply_action(task_id, payload.action.value)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    return task


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
