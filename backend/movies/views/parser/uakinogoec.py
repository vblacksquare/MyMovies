
import logging
from . import Parser
import json
import asyncio
import aiohttp
import bs4

from .browser import browser_ins, Browser
from ...models import Source, Movie, MovieEpisode, Translation, Socket

logger = logging.getLogger("movies")


class UakinogoecParser(Parser):
    source = Source.uakinogoec
    login_hash = None

    async def auth(self) -> tuple[aiohttp.ClientSession, dict]:
        session = aiohttp.ClientSession()

        async with session.get(
            url="https://uakinogo.ec/",
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:auth - {resp}")

        return session, {}

    async def _search(self, query: str) -> list[Movie]:
        async with self.session.get(
            url=f"https://uakinogo.ec/search/{query}",
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                          "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "priority": "u=0, i",
                "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "upgrade-insecure-requests": "1",
                "user-agent": self.user_agent,
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:search - {resp}")

            html = await resp.text()

        soup = bs4.BeautifulSoup(html, "html.parser")
        items = soup.select("div.shortstory")

        movies = []
        for item in items:
            external_id = item.get("id")

            img_el = item.select_one("div.shortstory__poster img")
            title_el = item.select_one("div.shortstory__title")
            link_el = item.select_one("a")
            description_el = item.select_one("div.excerpt")

            movies.append(Movie(
                external_id='-'.join((self.source.value, external_id)),
                title=title_el.get_text(strip=True),
                description=description_el.get_text(strip=True),
                poster="https://uakinogo.ec/" + img_el.get("data-src"),
                url=link_el["href"],
                source=self.source
            ))

        return movies

    async def _fill(self, movie: Movie) -> tuple[Movie, list[MovieEpisode]]:
        async def do(browser: Browser):
            data = {
                "playlist": None
            }

            def catch_socket(msg):
                if "PLAYLIST" in msg.text:
                    data["playlist"] = json.loads(msg.text.replace("PLAYLIST ", ""))

            await browser.context.add_init_script(f"""
            (() => {{
                const originalParse = JSON.parse;

                JSON.parse = function(str) {{
                    const data = originalParse(str);
                    if (data.length > 0 && data[0].title) {{
                        console.log('PLAYLIST', JSON.stringify(data));
                    }}
                    return data;
                }};
            }})();
            """)

            browser.context.on("console", catch_socket)
            if browser.page.url == movie.url:
                await browser.page.reload()
            else:
                await browser.page.goto(movie.url)

            title_el = await browser.page.query_selector("div.fullstory__title h1")
            description_el = await browser.page.query_selector("div.description__block")
            poster_el = await browser.page.query_selector("div.movie_poster img")

            movie.fill_title = await title_el.text_content()
            movie.fill_description = await description_el.text_content()
            movie.fill_poster = "https://uakinogo.ec/" + await poster_el.get_attribute("src")

            temp_iframe = await browser.page.query_selector("iframe")
            await temp_iframe.scroll_into_view_if_needed()

            iframe_element = await browser.page.wait_for_selector("iframe[src*='cinemar.cc']")
            await iframe_element.content_frame()

            while data["playlist"] is None:
                await asyncio.sleep(1)

            ua = await browser.page.evaluate("navigator.userAgent")
            sec_ch_ua = await browser.page.evaluate("""() => {
                if (!navigator.userAgentData) return 'not supported';
                return navigator.userAgentData.brands
                    .map(b => `"${b.brand}";v="${b.version}"`)
                    .join(', ');
            }""")

            if len(data["playlist"]) == 0:
                pass

            elif data["playlist"][0].get("id", "").startswith("s"):
                for season_obj in data["playlist"]:
                    season_i = int(season_obj["id"].split("s")[-1])

                    for episode_obj in season_obj["folder"]:
                        episode_i = int(episode_obj["id"].split("e")[-1])

                        for translation_obj in episode_obj["folder"]:
                            translation_id = translation_obj["id"]

                            if "img" in translation_obj["title"]:
                                translation_obj["title"] = translation_obj["title"].split('>')[-1]

                            translation = Translation(
                                external_id='-'.join([self.source.value, str(translation_obj["voice_id"])]),
                                title=translation_obj["title"],
                                meta={},
                            )

                            episode = MovieEpisode(
                                external_id='-'.join([
                                    translation.external_id,
                                    translation_id
                                ]),
                                movie=movie,
                                translation=translation,
                                season=season_i,
                                episode=episode_i,
                                meta={
                                    **translation_obj,
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

            else:
                for translation_obj in data["playlist"]:
                    translation_id = translation_obj["id"]

                    if "img" in translation_obj["title"]:
                        translation_obj["title"] = translation_obj["title"].split('>')[-1]

                    translation = Translation(
                        external_id='-'.join([self.source.value, str(translation_obj["voice_id"])]),
                        title=translation_obj["title"],
                        meta={},
                    )

                    episode = MovieEpisode(
                        external_id='-'.join([
                            translation.external_id,
                            translation_id
                        ]),
                        movie=movie,
                        translation=translation,
                        season=1,
                        episode=1,
                        meta={
                            **translation_obj,
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

        try:
            await asyncio.wait_for(browser_ins.execute(do), timeout=5)

        except Exception as err:
            logger.exception(err)

        return movie, episodes

    async def _fill_episode(self, episode: MovieEpisode) -> MovieEpisode:
        episode.stream = "https:" + episode.meta["file"]

        return episode
