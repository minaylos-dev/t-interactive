const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('trackball', {
	onDeltas: (cb) => {
		const listener = (event, deltas) => cb(deltas)
		ipcRenderer.on('sensor-deltas', listener)
		return () => ipcRenderer.removeListener('sensor-deltas', listener)
	}
})
