const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("alertActions", {
  select: (action) => {
    ipcRenderer.send("reminder-alert-action", action);
  }
});
