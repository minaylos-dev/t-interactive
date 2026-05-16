/**
 * This file will automatically be loaded by vite and run in the "renderer" context.
 * To learn more about the differences between the "main" and the "renderer" context in
 * Electron, visit:
 *
 * https://electronjs.org/docs/tutorial/process-model
 *
 * By default, Node.js integration in this file is disabled. When enabling Node.js integration
 * in a renderer process, please be aware of potential security implications. You can read
 * more about security risks here:
 *
 * https://electronjs.org/docs/tutorial/security
 *
 * To enable Node.js integration in this file, open up `main.js` and enable the `nodeIntegration`
 * flag:
 *
 * ```
 *  // Create the browser window.
 *  mainWindow = new BrowserWindow({
 *    width: 800,
 *    height: 600,
 *    webPreferences: {
 *      nodeIntegration: true
 *    }
 *  });
 * ```
 */

import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHashHistory } from 'vue-router';
import App from './App.vue';
import Home from './views/Home.vue';
import Quiz from './views/Quiz.vue';
import Result from './views/Result.vue';
import './index.css';
import TrackballGesture from './utils/trackballGesture'
import TrackballMove from './utils/trackballMove'

const routes = [
  { path: '/', component: Result },
  // { path: '/quiz', component: Quiz },
  // { path: '/result', component: Result },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

console.log(
  '👋 This message is being logged by "renderer.js", included via Vite',
);

// WebSocket client to Python server at ws://localhost:8765
const WS_URL = 'ws://localhost:8765';
let socket = null;
function connectWebSocket() {
  try {
    socket = new WebSocket(WS_URL);

    socket.addEventListener('open', () => {
      console.log('WebSocket connected to', WS_URL);
      // expose for debugging
      try { window.pythonWs = socket } catch (e) {}
      // send a hello/handshake message
      socket.send(JSON.stringify({ type: 'hello', ts: Date.now() }));
    });

    socket.addEventListener('message', (evt) => {
          // incoming data expected as JSON from Python server
          try {
            const data = JSON.parse(evt.data)
            // data expected: {rx, ry, rz, wx, wy, wz, ts}
              const tb = data && data.trackball ? data.trackball : data
              if (!tb) return
              // gesture detection (existing behavior)
              const gesture = window._trackGesture?.process(tb)
              if (gesture) {
                try {
                  window.dispatchEvent(new CustomEvent('trackball-gesture', { detail: gesture }))
                } catch (e) {
                  console.log('Failed to dispatch trackball-gesture event', e)
                }
              }
              // always dispatch raw move (no filtering) for immediate planet rotation
              try {
                const move = window._trackMove?.process(tb)
                if (move) window.dispatchEvent(new CustomEvent('trackball-move', { detail: move }))
              } catch (e) {
                console.log('Failed to dispatch trackball-move event', e)
              }
          } catch (err) {
            console.log('WebSocket message (raw):', evt.data, err)
          }
    });

    socket.addEventListener('close', (evt) => {
      console.log('WebSocket closed, reconnecting in 2000ms', evt.code, evt.reason);
      // try to reconnect after a short delay
      setTimeout(connectWebSocket, 2000);
    });

    socket.addEventListener('error', (err) => {
      console.error('WebSocket error', err);
      try { socket.close(); } catch (e) {}
    });
  } catch (err) {
    console.error('Failed to create WebSocket', err);
    setTimeout(connectWebSocket, 2000);
  }
}

connectWebSocket();

// create a gesture detector and expose it
window._trackGesture = new TrackballGesture({ windowSec: 0.6, xThresh: 0.5, yThresh: 0.5, zThresh: 0.5, cooldownMs: 600 })
// create a raw mover (no filtering) and expose it
window._trackMove = new TrackballMove()
