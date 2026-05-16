
import asyncio
import json
import os
import sys
import time

import websockets


def try_import_trackball():
    # Ensure the trackball directory is importable (it may not be a package).
    base = os.path.dirname(__file__)
    tb_dir = os.path.join(base, "trackball")
    if os.path.isdir(tb_dir) and tb_dir not in sys.path:
        sys.path.insert(0, tb_dir)
    try:
        import trackball_lib as tlib
        return tlib.Trackball
    except Exception as e:
        print(f"Trackball import failed: {e}")
        return None


CONNECTED = set()


async def handler(websocket, path=None):
    CONNECTED.add(websocket)
    try:
        await websocket.send(json.dumps({"msg": "Welcome from Python websocket server"}))
        async for message in websocket:
            print(f"Received from client: {message}")
            await websocket.send(json.dumps({"echo": message}))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED.discard(websocket)


async def broadcast_loop(trackball, interval=1/60):
    buffer = {}
    while True:
        if trackball is not None:
            data = {
                "rx": trackball.rx,
                "ry": trackball.ry,
                "rz": trackball.rz,
                "wx": round(trackball.wx, 5),
                "wy": round(trackball.wy, 5),
                "wz": round(trackball.wz, 5)
            }
        else:
            # fallback simulated data
            t = time.time()
            data = "trackball not found"

        if CONNECTED:
            payload = json.dumps({"trackball": data})
            websockets_to_remove = set()
            for ws in list(CONNECTED):
                if data != buffer or True:  # always send for now
                    try:
                        buffer = data
                        print(payload)
                        await ws.send(payload)
                    except Exception:
                        websockets_to_remove.add(ws)
            for ws in websockets_to_remove:
                CONNECTED.discard(ws)

        await asyncio.sleep(interval)


async def main():
    TrackballClass = try_import_trackball()
    tb = None
    if TrackballClass is not None:
        try:
            tb = TrackballClass()
            tb.start()
            print("Trackball started.")
        except Exception as e:
            print(f"Failed to start Trackball: {e}")
            tb = None

    async with websockets.serve(handler, "localhost", 8765):
        print("Server listening on ws://localhost:8765")
        broadcaster = asyncio.create_task(broadcast_loop(tb))
        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            broadcaster.cancel()


if __name__ == "__main__":
    asyncio.run(main())
