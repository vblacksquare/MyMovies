
import websockets
import json
import asyncio
import random
import time
from asgiref.sync import sync_to_async
from .socket import SocketHandler



class TheallohaSocketHandler(SocketHandler):
    domain = "absciss.thealloha.club"
    compact_sep = (',', ':')

    async def _idle(self):
        if self.temp["time"] is None:
            return

        diff = time.time() - self.temp["time"]
        print(diff)

        if diff >= 60:
            self.temp["current_time"] += diff * self.temp["speed"]

            payload = {
                "type": "playing",
                "current_time": self.temp["current_time"],
                "resolution": "480",
                "track_id": "1",
                "speed": self.temp["speed"],
                "subtitle": -1,
                "ts": self.now()
            }
            await self.ws.send(json.dumps(payload, separators=self.compact_sep))

    async def _start_connection(self) -> websockets.ClientConnection:
        self.temp = {
            "is_loaded": False,
            "time": None,
            "current_time": 0,
            "speed": 0.25
        }

        ws = await websockets.connect(
            self.socket.url,
            origin="https://absciss.thealloha.club",
            user_agent_header="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/145.0.0.0 Safari/537.36",
            open_timeout=20
        )

        payload = {
            "type": "playback_start",
            "current_time": self.temp["current_time"],
            "resolution": "480",
            "track_id": "1",
            "speed": 1,
            "subtitle": -1,
            "ts": self.now()
        }
        await ws.send(json.dumps(payload, separators=self.compact_sep))

        init_payload = {
            "type": "init",
            "current_time": self.temp["current_time"],
            "resolution": "480",
            "speed": 1,
            "subtitle": -1,
            "track_id": "1",
            "ts": self.now()
        }
        await ws.send(json.dumps(init_payload, separators=self.compact_sep))

        return ws

    async def on_data(self, data):
        payload = json.loads(data)

        self.socket.data = payload
        await sync_to_async(self.socket.save)()

        if not self.temp["is_loaded"]:
            self.temp["is_loaded"] = True
            self.temp["time"] = time.time()

            resumed_payload = {
                "type": "resumed",
                "current_time": self.temp["current_time"],
                "resolution": "480",
                "track_id": "1",
                "speed": self.temp["speed"],
                "subtitle": -1,
                "ts": self.now()
            }
            await self.ws.send(json.dumps(resumed_payload, separators=self.compact_sep))

            paused_payload = {
                "type": "paused",
                "current_time": self.temp["current_time"],
                "resolution": "480",
                "speed": self.temp["speed"],
                "subtitle": -1,
                "track_id": "1",
                "ts": self.now()
            }
            await self.ws.send(json.dumps(paused_payload, separators=self.compact_sep))

            await asyncio.sleep(random.uniform(1.0, 1.5))
            resumed_payload = {
                "type": "resumed",
                "current_time": self.temp["current_time"],
                "resolution": "480",
                "speed": self.temp["speed"],
                "subtitle": -1,
                "track_id": "1",
                "ts": self.now()
            }
            await self.ws.send(json.dumps(resumed_payload, separators=self.compact_sep))
