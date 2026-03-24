
import asyncio
import sys
import os
import platform
import subprocess
import logging
from playwright.async_api import async_playwright
from pathlib import Path
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from seleniumbase import cdp_driver

from movies.models import BrowserSession


logging.basicConfig(
    level=logging.DEBUG,
    encoding='utf-8',
    errors='replace'
)


system = platform.system()
HEADLESS = True


def get_user_data_dir():
    app_name = "MyMovies"

    if system == "Windows":
        base_path = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / app_name / "browser_profile"

    elif system == "Darwin":
        base_path = Path.home() / "Library" / "Application Support" / app_name / "browser_profile"

    else:
        base_path = Path.home() / "Library" / "Application Support" / app_name / "browser_profile"

    base_path.mkdir(parents=True, exist_ok=True)
    return str(base_path)


def get_executable_path(user_data_dir):
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent.parent / "app.asar.unpacked" / "backend" / "bin" / "chrome-stable"

    else:
        base_path = Path("bin/chrome-stable")

    if system == "Windows":
        chromium = list(base_path.glob("win_chrome.exe"))[0]

        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "win_chrome.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as err:
            pass

    elif system == "Darwin":
        chromium = list(base_path.glob("**/Google Chrome"))[0]

        try:
            subprocess.run(
                ["pkill", "-f", chromium],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except Exception as err:
            pass

    else:
        chromium = list(base_path.glob("**/Google Chrome"))[0]

    return chromium


class Command(BaseCommand):
    help = 'Start browser'

    def handle(self, *args, **options):
        asyncio.run(self.start_browser())

    async def start_browser(self):
        while True:
            try:
                user_data_dir = get_user_data_dir()
                driver = await cdp_driver.start_async(
                    browser_executable_path=get_executable_path(user_data_dir),
                    user_data_dir=user_data_dir,
                    incognito=False,
                    headless=False,
                    keep_user_data=True,
                    use_temp_dir=False,
                    args=[
                        "--no-first-run",
                        "--no-default-browser-check"
                    ]
                )

                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(driver.get_endpoint_url())

                    session = BrowserSession(url=driver.get_endpoint_url())
                    await sync_to_async(session.save)()

                    context = browser.contexts[0]
                    page = context.pages[0]

                    session = await context.new_cdp_session(page)
                    window = await session.send("Browser.getWindowForTarget")

                    while True:
                        bounds = await session.send("Browser.getWindowBounds", {
                            "windowId": window["windowId"]
                        })

                        if bounds["bounds"]["windowState"] == "minimized" or not HEADLESS:
                            await asyncio.sleep(0.1)
                            continue

                        await session.send("Browser.setWindowBounds", {
                            "windowId": window["windowId"],
                            "bounds": {
                                "windowState": "minimized"
                            }
                        })

            except Exception as err:
                self.stdout.write(self.style.ERROR(str(err)))
