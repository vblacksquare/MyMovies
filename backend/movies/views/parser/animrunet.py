
from . import Parser

import logging
import re
import asyncio
import aiohttp
import base64

from .browser import browser_ins, Browser
from ...models import Source, Movie, MovieEpisode, Translation, Socket

logger = logging.getLogger("movies")


class AnimrunetParser(Parser):
    source = Source.animrunet

    async def auth(self) -> tuple[aiohttp.ClientSession, dict]:
        self.session = aiohttp.ClientSession()
        return self.session, {}

    async def _search(self, query: str) -> list[Movie]:
        async def do(browser: Browser) -> list[Movie]:
            url = f"https://anim-ru.net/search.html?q={query.replace(' ', '+')}"

            if browser.page.url == url:
                await browser.page.reload(wait_until="domcontentloaded")
            else:
                await browser.page.goto(url, wait_until="domcontentloaded")

            try:
                await browser.page.locator("div.gsc-thumbnail-inside a.gs-title").first.wait_for(timeout=2000)

            except Exception as err:
                return

            results = await browser.page.query_selector_all("div.gsc-thumbnail-inside a.gs-title")
            for title_el in results:
                url = await title_el.get_attribute("href")

                if url is None or url.endswith("/"):
                    continue

                external_id = url.split("/")[-1]

                movies.append(Movie(
                    external_id='-'.join((self.source.value, external_id)),
                    title=await title_el.text_content(),
                    description=None,
                    poster=None,
                    url=url,
                    source=self.source
                ))

        movies = []
        await browser_ins.execute(do)
        return movies

    async def _fill(self, movie: Movie) -> tuple[Movie, list[MovieEpisode]]:
        async def do(browser: Browser) -> list[Movie]:
            if browser.page.url == movie.url:
                await browser.page.reload(wait_until="domcontentloaded")

            else:
                await browser.page.goto(movie.url, wait_until="domcontentloaded")

            poster_el = await browser.page.query_selector("img.poster")
            description_el = await browser.page.query_selector("div[itemprop='description']")

            movie.fill_title = await poster_el.get_attribute("alt")
            movie.fill_poster = await poster_el.get_attribute("src")
            movie.fill_description = await description_el.text_content()

            ua = await browser.page.evaluate("navigator.userAgent")
            sec_ch_ua = await browser.page.evaluate("""() => {
                if (!navigator.userAgentData) return 'not supported';
                return navigator.userAgentData.brands
                    .map(b => `"${b.brand}";v="${b.version}"`)
                    .join(', ');
            }""")

            pages = await browser.page.query_selector_all("select.sel_page option")
            for page in pages:
                page_value = await page.get_attribute("value")
                if page_value in ["", " "]:
                    continue

                translation = Translation(
                    external_id='-'.join([self.source.value, "Default"]),
                    title="Default",
                    meta={},
                )

                parts = page_value.split("-")

                if parts[0] == "/page" and parts[1] == "1":
                    page_value = '/' + '-'.join(parts[2:])

                episode = MovieEpisode(
                    external_id='-'.join([
                        translation.external_id,
                        page_value
                    ]),
                    movie=movie,
                    translation=translation,
                    season=1,
                    episode=int(parts[1]),
                    meta={
                        "url": "https://anim-ru.net" + page_value,
                        "stream_headers": {
                            "Accept": "*/*",
                            "Accept-Encoding": "gzip, deflate, br, zstd",
                            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Cache-Control": "no-cache",
                            "Pragma": "no-cache",
                            "Priority": "u=1, i",
                            "Sec-Ch-Ua": sec_ch_ua,
                            "Sec-Ch-Ua-Mobile": "?0",
                            "Sec-Ch-Ua-Platform": '"macOS"',
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "none",
                            "Sec-Fetch-Storage-Access": "active",
                            "User-Agent": ua
                        }
                    }
                )
                episodes.append(episode)

        episodes = []
        await browser_ins.execute(do)

        return movie, episodes

    async def _fill_episode(self, episode: MovieEpisode) -> MovieEpisode:
        async def do(browser: Browser) -> list[Movie]:
            statuses = {"player": None}

            async def catch_m3u8(response):
                if statuses['player']:
                    return

                if response.url.startswith("https://intrdb.com/player/"):
                    self.logger.info(response.url)

                elif response.url.startswith("https://armdb.org/player/"):
                    self.logger.info(response.url)

                else:
                    return

                html = await response.text()
                statuses['player'] = html

            browser.context.on("response", catch_m3u8)
            logger.info(str(episode.meta))
            if browser.page.url == episode.meta["url"]:
                return
            else:
                await browser.page.goto(episode.meta["url"], wait_until="domcontentloaded")

            while not statuses['player']:
                await asyncio.sleep(0.1)

            match = re.search(r'atob\("([^"]*)"\)', statuses['player'])
            logger.info(f"match: {match}")
            if match:
                encoded = match.group(1)

            else:
                return

            decoded = base64.b64decode(encoded).decode("utf-8")
            parts = decoded.split(",")

            best = 0
            stream = None

            for part in parts:
                quality, stream = part.split("]")
                quality = int(quality[1:-1])

                if quality > best:
                    best = quality
                    stream = stream

            episode.stream = stream

        await browser_ins.execute(do)

        return episode
