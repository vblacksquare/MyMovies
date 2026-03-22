
import asyncio
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async

from .sockets.socket import SocketHandler, get_handler
from movies.models import Socket


class Command(BaseCommand):
    help = 'Streamming socket immulation'

    def handle(self, *args, **options):
        asyncio.run(self.monitor_db())

    async def monitor_db(self):
        socket_handler: SocketHandler = None

        while True:
            await asyncio.sleep(.1)

            socket = await sync_to_async(
                lambda: Socket.objects.filter(is_active=True).order_by('-created_at').first()
            )()

            if not socket:
                if socket_handler:
                    await socket_handler.close()

                continue

            if socket_handler is None or socket.url != socket_handler.socket.url:
                if socket_handler:
                    await socket_handler.close()

                socket_handler = get_handler(socket, self.stdout, self.style)
                is_connected = await socket_handler.start_connection()

                if not is_connected:
                    socket_handler = None

            if socket_handler:
                is_ok = await socket_handler.idle()

                if not is_ok:
                    socket_handler = None
