import asyncio
import logging
import typing
from asgiref.sync import sync_to_async
from ...models import BrowserSession
from playwright.async_api import Page, BrowserContext, async_playwright

logger = logging.getLogger("movies")


class Browser:
    is_running: bool = False
    context: typing.Optional[BrowserContext] = None
    page: typing.Optional[Page] = None
    _lock = asyncio.Lock()

    async def start(self):
        if self.is_running:
            return

        self.is_running = True

    async def execute(self, func):
        async with self._lock:
            if not self.is_running:
                await self.start()

            browser_session = await sync_to_async(BrowserSession.objects.order_by('-created_at').first)()

            result = None
            async with async_playwright() as p:
                try:
                    browser = await p.chromium.connect_over_cdp(browser_session.url)

                    self.context = browser.contexts[0]
                    self.page = self.context.pages[0]

                    result = await func(self)

                    await browser.close()

                except Exception as err:
                    raise err

            logger.info("Task finished")
            return result

    async def stop(self):
        if not self.is_running:
            return

        self.is_running = False


browser_ins = Browser()
