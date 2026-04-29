const { app, BrowserWindow, dialog, ipcMain } = require("electron");
const { execFile, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");

const BACKEND_URL = process.env.RED_ROADMAP_API_URL || "http://127.0.0.1:8000";
let logFilePath = null;
let backendProcess = null;
let mainWindow = null;
let alertWindow = null;
let startupErrorWindow = null;
let reminderPollTimer = null;
let currentAlertMission = null;
let systemAlarmTimer = null;
const alertedReminderKeys = new Set();

app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");
app.setPath("userData", path.join(app.getPath("appData"), "Red Roadmap"));

function ensureLogFile() {
  if (logFilePath) {
    return logFilePath;
  }

  const logDir = path.join(app.getPath("userData"), "logs");
  fs.mkdirSync(logDir, { recursive: true });
  logFilePath = path.join(logDir, "main.log");
  return logFilePath;
}

function serializeLogValue(value) {
  if (value instanceof Error) {
    return {
      name: value.name,
      message: value.message,
      stack: value.stack
    };
  }
  return value;
}

function log(message, details = undefined) {
  try {
    const line = details === undefined
      ? `[${new Date().toISOString()}] ${message}\n`
      : `[${new Date().toISOString()}] ${message} ${JSON.stringify(serializeLogValue(details))}\n`;
    fs.appendFileSync(ensureLogFile(), line, "utf8");
  } catch (error) {
    // Logging must never become the startup failure.
  }
}

function logError(message, error) {
  log(message, error);
}

function formatError(error) {
  if (error instanceof Error) {
    return `${error.message}\n\n${error.stack || ""}`;
  }
  return String(error);
}

function errorHtml(title, body) {
  return `<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>${escapeHtml(title)}</title>
    <style>
      body {
        margin: 0;
        min-height: 100vh;
        background: #050713;
        color: #eaf1ff;
        font-family: "Segoe UI", system-ui, sans-serif;
        display: grid;
        place-items: center;
      }
      main {
        width: min(760px, calc(100vw - 48px));
        border: 1px solid #2f7ce8;
        border-radius: 8px;
        background: #0a1020;
        padding: 28px;
      }
      h1 {
        margin: 0 0 14px;
        color: #ff4fcf;
        font-size: 28px;
      }
      pre {
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        color: #c8d7f2;
        font: 13px Consolas, monospace;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>${escapeHtml(title)}</h1>
      <pre>${escapeHtml(body)}</pre>
    </main>
  </body>
</html>`;
}

function showStartupError(error) {
  const body = `${formatError(error)}\n\nLog file:\n${ensureLogFile()}`;
  logError("startup failed", error);

  if (!app.isReady()) {
    dialog.showErrorBox("Red Roadmap failed to start", body);
    return;
  }

  if (startupErrorWindow) {
    startupErrorWindow.focus();
    return;
  }

  startupErrorWindow = new BrowserWindow({
    width: 840,
    height: 560,
    minWidth: 640,
    minHeight: 420,
    backgroundColor: "#050713",
    title: "Red Roadmap startup error",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  startupErrorWindow.on("closed", () => {
    startupErrorWindow = null;
  });
  startupErrorWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHtml("Red Roadmap failed to start", body))}`);
}

process.on("uncaughtException", (error) => {
  showStartupError(error);
});

process.on("unhandledRejection", (reason) => {
  showStartupError(reason instanceof Error ? reason : new Error(`Unhandled rejection: ${String(reason)}`));
});

function rootPath() {
  return app.isPackaged ? process.resourcesPath : path.join(__dirname, "..");
}

function frontendEntry() {
  if (app.isPackaged) {
    return path.join(app.getAppPath(), "frontend", "dist", "index.html");
  }
  return "http://127.0.0.1:5173";
}

function envCandidates() {
  return [...new Set([
    path.join(app.getPath("userData"), ".env"),
    path.join(rootPath(), "backend", ".env"),
    path.join(rootPath(), "red_roadmap", ".env"),
    path.join(rootPath(), ".env"),
    path.join(process.resourcesPath || rootPath(), ".env")
  ])];
}

function logStartupContext() {
  log("startup context", {
    appIsPackaged: app.isPackaged,
    processResourcesPath: process.resourcesPath,
    dirname: __dirname,
    appPath: app.getAppPath(),
    userData: app.getPath("userData"),
    logFilePath: ensureLogFile(),
    backendUrl: BACKEND_URL
  });

  for (const candidate of envCandidates()) {
    log(".env candidate", {
      path: candidate,
      exists: fs.existsSync(candidate)
    });
  }
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
  const commandExists = fs.existsSync(config.command);
  log("starting backend", {
    command: config.command,
    args: config.args,
    cwd: config.cwd,
    exists: commandExists
  });
  if (!commandExists) {
    throw new Error(`Bundled backend executable was not found: ${config.command}`);
  }

  backendProcess = spawn(config.command, config.args, {
    cwd: config.cwd,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      RED_ROADMAP_APP_PATH: app.getAppPath(),
      RED_ROADMAP_RESOURCES_PATH: process.resourcesPath,
      RED_ROADMAP_USER_DATA: app.getPath("userData")
    }
  });

  backendProcess.stdout.on("data", (data) => {
    log("backend stdout", data.toString().trimEnd());
  });
  backendProcess.stderr.on("data", (data) => {
    log("backend stderr", data.toString().trimEnd());
  });
  backendProcess.on("error", (error) => {
    logError("backend spawn error", error);
  });
  backendProcess.on("exit", (code, signal) => {
    log("backend exited", { code, signal });
    backendProcess = null;
  });
}

function checkBackend() {
  return backendReady();
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function waitForBackend(timeoutMs = 30000) {
  const started = Date.now();
  let attempts = 0;
  return new Promise((resolve, reject) => {
    const check = async () => {
      attempts += 1;
      const status = await backendStatus(attempts);
      if (status === "ready") {
        log("backend health ready", { attempts });
        resolve();
      } else {
        retry();
      }
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

async function backendReady() {
  return (await backendStatus()) === "ready";
}

async function backendStatus(attempt = undefined) {
  const healthUrl = `${BACKEND_URL}/health`;
  const openapiUrl = `${BACKEND_URL}/openapi.json`;
  try {
    const health = await fetch(healthUrl);
    log("backend health check", {
      attempt,
      url: healthUrl,
      status: health.status,
      ok: health.ok
    });
    if (!health.ok) {
      log("backend health response body", {
        attempt,
        body: await health.text().catch((error) => `Unable to read response body: ${error.message}`)
      });
      return "down";
    }

    const openapi = await fetch(openapiUrl);
    log("backend openapi check", {
      attempt,
      url: openapiUrl,
      status: openapi.status,
      ok: openapi.ok
    });
    if (!openapi.ok) {
      log("backend openapi response body", {
        attempt,
        body: await openapi.text().catch((error) => `Unable to read response body: ${error.message}`)
      });
      return "down";
    }

    const schema = await openapi.json();
    const hasDueRoute = Boolean(schema?.paths?.["/api/reminders/due"]);
    log("backend schema check", {
      attempt,
      hasDueRoute
    });
    return hasDueRoute ? "ready" : "stale";
  } catch (error) {
    logError("backend health check failed", error);
    return "down";
  }
}

async function createWindow() {
  logStartupContext();
  const status = await backendStatus();
  log("initial backend status", { status });
  if (status !== "ready") {
    if (status === "stale" && !app.isPackaged && isLocalBackendUrl()) {
      await stopStaleBackendListener();
    }
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
  mainWindow.webContents.on("render-process-gone", (_event, details) => {
    log("render-process-gone", details);
  });
  mainWindow.webContents.on("child-process-gone", (_event, details) => {
    log("webContents child-process-gone", details);
  });

  const frontend = frontendEntry();
  log("loading frontend", {
    path: frontend,
    packaged: app.isPackaged,
    exists: app.isPackaged ? fs.existsSync(frontend) : undefined
  });
  if (app.isPackaged) {
    if (!fs.existsSync(frontend)) {
      throw new Error(`Built frontend was not found: ${frontend}`);
    }
    await mainWindow.loadFile(frontend);
  } else {
    await mainWindow.loadURL(frontend);
  }

  startReminderPolling();
}

function isLocalBackendUrl() {
  try {
    const url = new URL(BACKEND_URL);
    return ["127.0.0.1", "localhost"].includes(url.hostname);
  } catch {
    return false;
  }
}

function backendPort() {
  try {
    return new URL(BACKEND_URL).port || "8000";
  } catch {
    return "8000";
  }
}

function execFileAsync(command, args) {
  return new Promise((resolve) => {
    execFile(command, args, { windowsHide: true }, (error, stdout, stderr) => {
      resolve({ error, stdout, stderr });
    });
  });
}

async function stopStaleBackendListener() {
  const port = backendPort();
  if (process.platform !== "win32") {
    return;
  }

  const script = `
    $connections = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
      Write-Output $connection.OwningProcess
      Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
      Get-CimInstance Win32_Process -Filter "ParentProcessId=$($connection.OwningProcess)" -ErrorAction SilentlyContinue |
        ForEach-Object {
          Write-Output $_.ProcessId
          Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
  `;
  const result = await execFileAsync("powershell.exe", ["-NoProfile", "-Command", script]);
  return result;
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
    const { reminders } = await fetchDueReminders();

    if (!Array.isArray(reminders) || !reminders.length) {
      return;
    }

    const mission = reminders.find((item) => !alertedReminderKeys.has(reminderKey(item)));
    if (mission) {
      createAlertWindow(mission);
    }
  } catch (error) {
    // Keep polling on the next interval.
  }
}

async function fetchDueReminders() {
  const dueUrl = `${BACKEND_URL}/api/reminders/due`;
  const dueResponse = await fetch(dueUrl, {
    headers: {
      "Content-Type": "application/json"
    }
  });

  if (dueResponse.ok) {
    return {
      status: dueResponse.status,
      reminders: await dueResponse.json()
    };
  }

  return {
    status: dueResponse.status,
    reminders: []
  };
}

function reminderKey(mission) {
  return `${mission.id}:${mission.next_check_at || mission.reminder_at || mission.status || ""}`;
}

function createAlertWindow(mission) {
  if (alertWindow) {
    alertWindow.show();
    alertWindow.setAlwaysOnTop(true, "screen-saver");
    alertWindow.focus();
    return;
  }

  currentAlertMission = mission;

  const key = reminderKey(mission);

  alertWindow = new BrowserWindow({
    fullscreen: true,
    resizable: false,
    minimizable: false,
    maximizable: false,
    alwaysOnTop: true,
    center: true,
    backgroundColor: "#050806",
    show: false,
    title: "Mission Alert",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "alert-preload.js")
    }
  });
  alertWindow.webContents.setAudioMuted(false);

  alertWindow.once("ready-to-show", () => {
    alertedReminderKeys.add(key);
    alertWindow.setAlwaysOnTop(true, "screen-saver");
    alertWindow.show();
    alertWindow.focus();
    startSystemAlarm(mission, key);
  });
  alertWindow.on("blur", () => {
    if (alertWindow) {
      alertWindow.focus();
    }
  });
  alertWindow.on("closed", () => {
    stopSystemAlarm();
    alertWindow = null;
    currentAlertMission = null;
  });

  alertWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(alertHtml({
    mission
  }))}`);
}

function startSystemAlarm(mission, key) {
  stopSystemAlarm();
  playSystemAlarmOnce(mission, key);
  systemAlarmTimer = setInterval(() => playSystemAlarmOnce(mission, key), 1400);
}

function stopSystemAlarm() {
  if (systemAlarmTimer) {
    clearInterval(systemAlarmTimer);
    systemAlarmTimer = null;
  }
}

function playSystemAlarmOnce(mission, key) {
  if (process.platform === "win32") {
    execFile(
      "powershell.exe",
      [
        "-NoProfile",
        "-Command",
        "try { [console]::beep(1000, 450) } catch {}; Start-Sleep -Milliseconds 650"
      ],
      { windowsHide: true }
    );
    return;
  }

  process.stdout.write("\u0007");
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

function alertHtml({ mission }) {
  const title = escapeHtml(mission?.title || "Untitled mission");
  const priority = escapeHtml(mission?.priority || "MEDIUM");
  const mode = escapeHtml(String(mission?.mode || "FLEXIBLE").replace("_", " "));
  const alarmAt = escapeHtml(formatReminderTime(mission?.next_check_at || mission?.reminder_at));

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
        background:
          radial-gradient(circle at top left, rgba(198, 154, 73, 0.14), transparent 34rem),
          linear-gradient(135deg, #050806 0%, #0b130d 48%, #12180f 100%);
        color: #f3ead7;
        font-family: Inter, "Segoe UI", system-ui, sans-serif;
      }
      main {
        width: min(920px, calc(100vw - 48px));
        border: 1px solid #3a422f;
        border-radius: 8px;
        background: rgba(17, 26, 18, 0.94);
        padding: 48px;
        box-shadow: 0 18px 60px rgba(0, 0, 0, 0.38), 0 0 26px rgba(198, 154, 73, 0.16);
      }
      .label {
        margin-bottom: 10px;
        color: #b7aa8a;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0 0 12px;
        color: #eadfb7;
        font-size: clamp(48px, 8vw, 96px);
        line-height: 1.1;
      }
      p {
        margin: 0 0 30px;
        color: #b7aa8a;
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
        border: 1px solid #3a422f;
        border-radius: 8px;
        background: rgba(26, 36, 24, 0.9);
        padding: 14px 16px;
      }
      .meta-label {
        color: #b7aa8a;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .meta-value {
        margin-top: 6px;
        color: #f3ead7;
        font-size: 16px;
        font-weight: 900;
      }
      .warning {
        margin: 0 0 24px;
        border: 1px solid #c69a49;
        border-radius: 8px;
        background: rgba(198, 154, 73, 0.12);
        color: #eadfb7;
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
        border: 1px solid #3a422f;
        border-radius: 8px;
        background: #1a2418;
        color: #f3ead7;
        font: inherit;
        font-size: 16px;
        font-weight: 900;
        cursor: pointer;
      }
      button.primary {
        border-color: #b7a85b;
        background: #b7a85b;
        color: #07100b;
        box-shadow: 0 0 26px rgba(198, 154, 73, 0.16);
      }
      button:hover {
        border-color: #eadfb7;
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
          <div class="meta-label">Alarm Time</div>
          <div class="meta-value">${alarmAt}</div>
        </div>
      </div>
      <div class="actions">
        <button class="primary" onclick="selectAction('start')">Start</button>
        <button onclick="selectAction('snooze')">Snooze</button>
        <button onclick="selectAction('away')">Away</button>
        <button onclick="selectAction('complete')">Complete</button>
      </div>
    </main>
    <script>
      function selectAction(action) {
        window.alertActions.select(action);
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
        body: JSON.stringify({ minutes: 10 })
      });
    } else if (action === "away") {
      await requestJson(`/api/missions/${mission.id}/alert-action`, {
        method: "POST",
        body: JSON.stringify({ action: "away" })
      });
    } else {
      return;
    }
  } catch (error) {
    // The alert still closes; the next poll will retry if the mission remains due.
  }
}

ipcMain.on("reminder-alert-action", async (_event, action) => {
  stopSystemAlarm();
  await applyReminderAction(action);
  if (alertWindow) {
    alertWindow.close();
  }
});

app.whenReady().then(() => {
  createWindow().catch((error) => {
    showStartupError(error);
  });
});

app.on("child-process-gone", (_event, details) => {
  log("app child-process-gone", details);
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
