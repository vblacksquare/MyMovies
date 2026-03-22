
import websockets
import asyncio
import time
from asgiref.sync import sync_to_async
from abc import ABC, abstractmethod

from movies.models import Socket


class SocketHandler(ABC):
    domain: str
    socket: Socket
    temp: dict
    ws: websockets.ClientConnection

    timeout_idle: float = 5.0

    def __init__(self, socket: Socket, stdout, stdout_style) -> None:
        self.socket = socket
        self.stdout = stdout
        self.stdout_style = stdout_style

    @staticmethod
    def now():
        return int(time.time() * 1000)

    @abstractmethod
    async def _start_connection(self) -> websockets.ClientConnection:
        pass

    async def start_connection(self) -> bool:
        self.stdout.write(self.stdout_style.NOTICE(f"Connecting socket: {self.socket.url}"))

        try:
            self.ws = await self._start_connection()
            self.stdout.write(self.stdout_style.SUCCESS(f"Connected to socket: {self.socket.url}"))

            return True

        except Exception as err:
            self.stdout.write(self.stdout_style.ERROR(f"Can't connect to socket: {self.socket.url}"))

            return False

    async def _idle(self):
        pass

    async def idle(self):
        try:
            await self._idle()
            message = await asyncio.wait_for(self.ws.recv(), timeout=self.timeout_idle)
            await self._on_data(message)
            self.stdout.write(self.stdout_style.SUCCESS(f"Data received: {message}"))

            return True

        except asyncio.TimeoutError:
            return True

        except websockets.exceptions.ConnectionClosed:
            self.stdout.write(self.stdout_style.ERROR(f"Connectiong closed by server: {self.socket.url}"))

            self.socket.is_active = False
            await sync_to_async(self.socket.save)()
            return False

    async def _on_data(self, data):
        pass

    async def close(self):
        if self.ws:
            await self.ws.close()
            self.stdout.write(self.stdout_style.NOTICE("Socket closed"))


from .thealloha import TheallohaSocketHandler


def get_handler(socket: Socket, stdout, stdout_style) -> SocketHandler:
    for cls in SocketHandler.__subclasses__():
        if cls.domain in socket.url:
            return cls(socket, stdout=stdout, stdout_style=stdout_style)

    return None
