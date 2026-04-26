const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");
const { pathToFileURL } = require("url");

const BACKEND_URL = process.env.RED_ROADMAP_API_URL || "http://127.0.0.1:8000";
let backendProcess = null;
let mainWindow = null;
let alertWindow = null;
let reminderPollTimer = null;
let currentAlertMission = null;
const alertedReminderKeys = new Set();

app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");

function rootPath() {
  return app.isPackaged ? process.resourcesPath : path.join(__dirname, "..");
}

function backendCommand() {
  if (app.isPackaged) {
    const exe = process.platform === "win32" ? "RedRoadmapBackend.exe" : "RedRoadmapBackend";
    return {
      command: path.join(process.resourcesPath, "backend", exe),
      args: [],
      cwd: process.resourcesPath
    };
  }

  const venvPython = process.platform === "win32"
    ? path.join(rootPath(), ".venv", "Scripts", "python.exe")
    : path.join(rootPath(), ".venv", "bin", "python");
  const python = process.env.PYTHON || (fs.existsSync(venvPython) ? venvPython : (process.platform === "win32" ? "python" : "python3"));
  return {
    command: python,
    args: ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd: rootPath()
  };
}

function startBackend() {
  const config = backendCommand();
  backendProcess = spawn(config.command, config.args, {
    cwd: config.cwd,
    windowsHide: true,
    stdio: app.isPackaged ? "ignore" : "inherit",
    env: {
      ...process.env
    }
  });

  backendProcess.on("exit", () => {
    backendProcess = null;
  });
}

function checkBackend() {
  return new Promise((resolve) => {
    const request = http.get(`${BACKEND_URL}/health`, (response) => {
      response.resume();
      resolve(response.statusCode === 200);
    });
    request.on("error", () => resolve(false));
    request.setTimeout(1000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function waitForBackend(timeoutMs = 30000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const request = http.get(`${BACKEND_URL}/health`, (response) => {
        response.resume();
        if (response.statusCode === 200) {
          resolve();
        } else {
          retry();
        }
      });
      request.on("error", retry);
      request.setTimeout(1000, () => {
        request.destroy();
        retry();
      });
    };

    const retry = () => {
      if (Date.now() - started > timeoutMs) {
        reject(new Error("Backend did not become available."));
        return;
      }
      setTimeout(check, 500);
    };

    check();
  });
}

async function createWindow() {
  if (!(await checkBackend())) {
    startBackend();
  }
  await waitForBackend();

  mainWindow = new BrowserWindow({
    width: 1480,
    height: 920,
    minWidth: 1120,
    minHeight: 720,
    backgroundColor: "#050713",
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.once("ready-to-show", () => mainWindow.show());
  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  if (app.isPackaged) {
    await mainWindow.loadFile(path.join(app.getAppPath(), "frontend", "dist", "index.html"));
  } else {
    await mainWindow.loadURL("http://127.0.0.1:5173");
  }

  startReminderPolling();
}

function startReminderPolling() {
  stopReminderPolling();
  pollDueReminders();
  reminderPollTimer = setInterval(pollDueReminders, 30000);
}

function stopReminderPolling() {
  if (reminderPollTimer) {
    clearInterval(reminderPollTimer);
    reminderPollTimer = null;
  }
}

async function pollDueReminders() {
  try {
    const reminders = await requestJson("/api/reminders/due");
    if (!Array.isArray(reminders) || !reminders.length) {
      return;
    }

    const mission = reminders.find((item) => !alertedReminderKeys.has(reminderKey(item)));
    if (mission) {
      createAlertWindow(mission);
    }
  } catch (error) {
    console.error("Reminder polling failed:", error);
  }
}

function reminderKey(mission) {
  return `${mission.id}:${mission.reminder_at || ""}`;
}

function createAlertWindow(mission) {
  if (alertWindow) {
    alertWindow.show();
    alertWindow.setAlwaysOnTop(true, "screen-saver");
    alertWindow.focus();
    return;
  }

  currentAlertMission = mission;
  alertedReminderKeys.add(reminderKey(mission));

  const alarmPath = path.join(__dirname, "assets", "alarm.mp3");
  const alarmExists = fs.existsSync(alarmPath);

  alertWindow = new BrowserWindow({
    fullscreen: true,
    resizable: false,
    minimizable: false,
    maximizable: false,
    alwaysOnTop: true,
    center: true,
    backgroundColor: "#050713",
    show: false,
    title: "Mission Alert",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "alert-preload.js")
    }
  });

  alertWindow.once("ready-to-show", () => {
    alertWindow.setAlwaysOnTop(true, "screen-saver");
    alertWindow.show();
    alertWindow.focus();
  });
  alertWindow.on("blur", () => {
    if (alertWindow) {
      alertWindow.focus();
    }
  });
  alertWindow.on("closed", () => {
    alertWindow = null;
    currentAlertMission = null;
  });

  alertWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(alertHtml({
    mission,
    alarmSrc: alarmExists ? pathToFileURL(alarmPath).href : "",
    alarmExists
  }))}`);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatReminderTime(value) {
  if (!value) {
    return "No reminder time";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function alertHtml({ mission, alarmSrc, alarmExists }) {
  const title = escapeHtml(mission?.title || "Untitled mission");
  const priority = escapeHtml(mission?.priority || "MEDIUM");
  const mode = escapeHtml(String(mission?.mode || "FLEXIBLE").replace("_", " "));
  const reminderAt = escapeHtml(formatReminderTime(mission?.reminder_at));

  return `<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Mission Alert</title>
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: #050713;
        color: #eaf1ff;
        font-family: Inter, "Segoe UI", system-ui, sans-serif;
      }
      main {
        width: min(920px, calc(100vw - 48px));
        border: 1px solid #2f7ce8;
        border-radius: 8px;
        background: #0a1020;
        padding: 48px;
        box-shadow: 0 18px 60px rgba(0, 0, 0, 0.45), 0 0 28px rgba(255, 79, 207, 0.18);
      }
      .label {
        margin-bottom: 10px;
        color: #91a7d0;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0 0 12px;
        color: #ff4fcf;
        font-size: clamp(48px, 8vw, 96px);
        line-height: 1.1;
      }
      p {
        margin: 0 0 30px;
        color: #91a7d0;
        font-size: 18px;
        font-weight: 600;
      }
      .meta {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 0 0 24px;
      }
      .meta-item {
        border: 1px solid #263b72;
        border-radius: 8px;
        background: #0e1830;
        padding: 14px 16px;
      }
      .meta-label {
        color: #91a7d0;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .meta-value {
        margin-top: 6px;
        color: #eaf1ff;
        font-size: 16px;
        font-weight: 900;
      }
      .warning {
        margin: 0 0 24px;
        border: 1px solid #fbbf24;
        border-radius: 8px;
        background: rgba(251, 191, 36, 0.12);
        color: #fde68a;
        padding: 14px 16px;
        font-size: 15px;
        font-weight: 800;
      }
      .actions {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
      }
      button {
        height: 56px;
        border: 1px solid #2f7ce8;
        border-radius: 8px;
        background: #0e1830;
        color: #eaf1ff;
        font: inherit;
        font-size: 16px;
        font-weight: 900;
        cursor: pointer;
      }
      button.primary {
        border-color: #ff4fcf;
        background: #ff4fcf;
        color: #050713;
        box-shadow: 0 0 26px rgba(255, 79, 207, 0.22);
      }
      button:hover {
        border-color: #ff86dd;
      }
      @media (max-width: 720px) {
        main {
          padding: 28px;
        }
        .meta {
          grid-template-columns: 1fr;
        }
        .actions {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <div class="label">Reminder</div>
      <h1>${title}</h1>
      <p>A mission reminder is due.</p>
      <div class="meta">
        <div class="meta-item">
          <div class="meta-label">Priority</div>
          <div class="meta-value">${priority}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Mode</div>
          <div class="meta-value">${mode}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Reminder Time</div>
          <div class="meta-value">${reminderAt}</div>
        </div>
      </div>
      ${alarmExists ? `<audio id="alarm" src="${alarmSrc}" loop preload="auto"></audio>` : `<div class="warning">Alarm file missing: desktop/assets/alarm.mp3</div>`}
      <div class="actions">
        <button class="primary" onclick="selectAction('start')">Start</button>
        <button onclick="selectAction('snooze')">Snooze</button>
        <button onclick="selectAction('complete')">Complete</button>
        <button onclick="selectAction('dismiss')">Dismiss</button>
      </div>
    </main>
    <script>
      const alarm = document.getElementById("alarm");

      function stopAlarm() {
        if (!alarm) return;
        alarm.pause();
        alarm.currentTime = 0;
      }

      function selectAction(action) {
        stopAlarm();
        window.alertActions.select(action);
      }

      window.addEventListener("beforeunload", stopAlarm);

      if (alarm) {
        alarm.play().catch((error) => {
          console.warn("Alarm playback failed", error);
        });
      }
    </script>
  </body>
</html>`;
}

async function requestJson(pathname, options = {}) {
  const response = await fetch(`${BACKEND_URL}${pathname}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function applyReminderAction(action) {
  const mission = currentAlertMission;
  if (!mission) {
    return;
  }

  try {
    if (action === "start") {
      await requestJson(`/api/missions/${mission.id}/start`, { method: "POST" });
    } else if (action === "complete") {
      await requestJson(`/api/missions/${mission.id}/complete`, {
        method: "POST",
        body: JSON.stringify({ completed: true })
      });
    } else if (action === "snooze") {
      await requestJson(`/api/missions/${mission.id}/snooze`, {
        method: "POST",
        body: JSON.stringify({ minutes: 5 })
      });
    } else if (action !== "dismiss") {
      console.warn(`Unknown reminder action: ${action}`);
    }
    console.log(`Reminder action: ${action} for mission ${mission.id}`);
  } catch (error) {
    console.error(`Reminder action failed: ${action}`, error);
  }
}

ipcMain.on("reminder-alert-action", async (_event, action) => {
  await applyReminderAction(action);
  if (alertWindow) {
    alertWindow.close();
  }
});

app.whenReady().then(() => {
  createWindow().catch((error) => {
    console.error(error);
    app.quit();
  });
});

app.on("window-all-closed", () => {
  stopReminderPolling();
  stopBackend();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  stopReminderPolling();
  stopBackend();
});
