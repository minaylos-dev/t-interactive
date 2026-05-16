# Python WebSocket Server

This is a minimal Python WebSocket server you can connect to from an Electron app (or a browser) on the same machine.

Quick start

1. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server:

```bash
python server.py
```

The server listens on `ws://localhost:8765`.

Electron sample (renderer process)

```javascript
const ws = new WebSocket('ws://localhost:8765');
ws.onopen = () => ws.send('Hello from Electron');
ws.onmessage = (ev) => console.log('Server:', ev.data);
```

You can also open `client.html` in a browser or load it in Electron to test locally.
