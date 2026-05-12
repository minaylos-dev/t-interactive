import { app, BrowserWindow } from 'electron';
import path from 'node:path';
import started from 'electron-squirrel-startup';

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (started) {
  app.quit();
}

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  }

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
  return mainWindow
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(async () => {
  const mainWindow = createWindow();

  // Try to dynamically load `node-hid` and attach simple sensor reader.
  try {
    const mod = await import('node-hid')
    const HID = mod.default ?? mod
    const devices = HID.devices()
    const mouseDevices = devices.filter(d => d.usagePage === 1 && d.usage === 2)
    const sensorPaths = mouseDevices.slice(0, 3).map(d => d.path)

    if (sensorPaths.length > 0) {
      const hidDevices = sensorPaths.map(p => new HID.HID(p))
      const deltas = [0, 0, 0, 0, 0, 0]

      hidDevices.forEach((device, index) => {
        device.on('data', (data) => {
          try {
            const dx = data.readInt8(1)
            const dy = data.readInt8(2)
            deltas[index * 2] += dx
            deltas[index * 2 + 1] += dy
          } catch (err) {
            // ignore parse errors for unknown report formats
          }
        })
        device.on('error', (err) => console.error('HID device error', err))
      })

      const flushId = setInterval(() => {
        if (deltas.some(v => v !== 0)) {
          try {
            mainWindow.webContents.send('sensor-deltas', [...deltas])
          } catch (e) {
            /* ignore if window gone */
          }
          deltas.fill(0)
        }
      }, 1000 / 60)

      // store references for cleanup
      app._hid = { hidDevices, flushId }
    }
  } catch (err) {
    console.log('node-hid not available or failed to initialize:', err.message || err)
  }

  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('will-quit', () => {
  if (app._hid) {
    clearInterval(app._hid.flushId)
    app._hid.hidDevices.forEach(d => { try { d.close() } catch (e) {} })
  }
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
