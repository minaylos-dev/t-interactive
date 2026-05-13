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
