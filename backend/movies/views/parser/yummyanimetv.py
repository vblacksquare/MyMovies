import time
import logging
from . import Parser
from asgiref.sync import sync_to_async
import json
import asyncio
import aiohttp
import re
import bs4

from .browser import browser_ins, Browser
from ...models import Source, Movie, MovieEpisode, Translation, Socket


logger = logging.getLogger("movies")


class YummyanimetvParser(Parser):
    source = Source.yummyanimetv
    login_hash = None

    async def auth(self) -> tuple[aiohttp.ClientSession, dict]:
        session = aiohttp.ClientSession()

        async with session.get(
            url="https://yummyanime.tv/",
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:auth - {resp}")

            html = await resp.text()

            match = re.search(r"dle_login_hash\s*=\s*'([^']+)'", html)
            user_hash = match.group(1)

        return session, {"user_hash": user_hash}

    async def _search(self, query: str) -> list[Movie]:
        async with self.session.post(
            url="https://yummyanime.tv/index-2",
            data={
                "do": "search",
                "subaction": "search",
                "story": query
            },
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://yummyanime.tv",
                "pragma": "no-cache",
                "priority": "u=0, i",
                "referer": "https://yummyanime.tv/index-2",
                "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": self.user_agent,
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:search - {resp}")

            html = await resp.text()

        soup = bs4.BeautifulSoup(html, "html.parser")
        items = soup.select("div.movie-item")

        movies = []
        for item in items:
            img_el = item.select_one("img")
            title_el = item.select_one("div.movie-item__title")
            link_el = item.select_one("a.movie-item__link")
            external_id = link_el['href'].split('/')[-1].split('.')[0]

            movies.append(Movie(
                external_id='-'.join((self.source.value, external_id)),
                title=title_el.get_text(strip=True),
                description=None,
                poster="https://yummyanime.tv" + img_el["src"],
                url=link_el["href"],
                source=self.source
            ))

        return movies

    async def _fill_alohaplayer(self, movie: Movie, external_id: int) -> tuple[Movie, list[MovieEpisode]]:
        async with self.session.get(
            url="https://yummyanime.tv/engine/ajax/controller.php",
            params={
                "mod": "alloha-player",
                "url": "1",
                "action": "iframe",
                "id": external_id
            },
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            data = await resp.json()

            player_url = data['data']

        player_data = {
            "url": player_url,
            "translations": []
        }

        movie.meta["player_urls"].append(player_data)

        async with self.session.get(
            url=player_url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Priority": "u=0, i",
                "Referer": "https://yummyanime.tv/",
                "Sec-Ch-Ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Storage-Access": "active",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": self.user_agent,
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            html = await resp.text()

        pattern = r"const\s+(\w+)\s*=\s*JSON\.parse\('\s*(\{[\s\S]*?\})\s*'\)"

        extracted_data = {}
        for match in re.finditer(pattern, html):
            var_name = match.group(1)
            json_str = match.group(2)

            try:
                extracted_data[var_name] = json.loads(json_str)
            except json.JSONDecodeError as err:
                self.logger.exception(err)

        config_data = extracted_data["config"]
        filelist_data = extracted_data["fileList"]

        movie.fill_title = config_data["mediaMetadata"].get("title", movie.fill_title)

        episodes = []

        for season_key in filelist_data["all"]:
            season = filelist_data["all"][season_key]

            for episode_key in season:
                episode = season[episode_key]

                for translation_key in episode:
                    translation = episode[translation_key]

                    trans = Translation(
                        external_id='-'.join([self.source.value, translation_key]),
                        title=translation["translation"],
                        meta={"id": translation["id_translation"]}
                    )
                    player_data["translations"].append(trans.external_id)

                    ep = MovieEpisode(
                        external_id='-'.join([
                            self.source.value, translation_key,
                            str(translation["id"]), str(external_id)
                        ]),
                        movie=movie,
                        translation=trans,
                        season=int(season_key),
                        episode=int(episode_key),
                        meta=translation
                    )
                    episodes.append(ep)

        return movie, episodes

    async def _fill_xfplayer_ukranian(self, movie: Movie, external_id: int) -> tuple[Movie, list[MovieEpisode]]:
        async with self.session.get(
            url="https://yummyanime.tv/engine/ajax/controller.php",
            params={
                "mod": "xfplayer",
                "url": "1",
                "name": "ashdi",
                "id": external_id
            },
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            data = await resp.json()

            player_url = data['data']

        player_data = {
            "url": player_url,
            "translations": []
        }

        movie.meta["player_urls"].append(player_data)

        async with self.session.get(
            url=player_url,
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            html = await resp.text()

        regex = r"file:\s*'([\s\S]*?)'(?=\s*[,}\n;])"
        match = re.search(regex, html)

        if not match:
            return Movie, []

        data = json.loads(match.group(1))
        episodes = []

        for translation_obj in data:
            for season_obj in translation_obj["folder"]:
                translation = Translation(
                    external_id='-'.join([self.source.value, 'ashdi', translation_obj["title"].lower().strip()]),
                    title=' '.join([translation_obj['title'].strip(), "🇺🇦"]),
                    meta={}
                )
                player_data["translations"].append(translation.external_id)

                season_i = ""
                for char in season_obj["title"]:
                    if char.isdigit():
                        season_i += char

                for episode_obj in season_obj["folder"]:

                    episode_i = ""
                    for char in episode_obj["title"]:
                        if char.isdigit():
                            episode_i += char

                    ep = MovieEpisode(
                        external_id='-'.join([
                            translation.external_id,
                            episode_obj['id'], episode_obj['vid']
                        ]),
                        movie=movie,
                        translation=translation,
                        season=int(season_i),
                        episode=int(episode_i),
                        meta=episode_obj
                    )
                    episodes.append(ep)

        return movie, episodes

    async def _fill_xfplayer_russian(self, movie: Movie, external_id: int) -> tuple[Movie, list[MovieEpisode]]:
        async with self.session.get(
            url="https://yummyanime.tv/engine/ajax/controller.php",
            params={
                "mod": "xfplayer",
                "url": "1",
                "name": "parlorate",
                "id": external_id
            },
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            data = await resp.json()

            player_url = data['data']

        player_data = {
            "url": player_url,
            "translations": []
        }

        movie.meta["player_urls"].append(player_data)

        async with self.session.get(
            url=player_url,
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            },
            allow_redirects=True
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            html = await resp.text()

        soup = bs4.BeautifulSoup(html, "html.parser")
        data_el = soup.select_one("#inputData")

        if not data_el:
            return movie, []

        data = json.loads(data_el.get_text())

        episodes = []

        for season_key in data:
            seasons = data[season_key]

            for episode_key in seasons:
                episode_objs = seasons[episode_key]

                for episode_obj in episode_objs:
                    translation = Translation(
                        external_id='-'.join([self.source.value, 'parlorate', str(episode_obj['voice_id'])]),
                        title=' '.join([episode_obj['voice_name'], "ru"]),
                        meta={"id": episode_obj["voice_id"]},
                    )
                    player_data["translations"].append(translation.external_id)

                    episode = MovieEpisode(
                        external_id='-'.join([
                            translation.external_id,
                            str(episode_obj['video_id'])
                        ]),
                        movie=movie,
                        translation=translation,
                        season=int(season_key),
                        episode=int(episode_key),
                        meta=episode_obj
                    )
                    episodes.append(episode)

        return movie, episodes

    async def _fill_kodikplayer(self, movie: Movie, external_id: int) -> tuple[Movie, list[MovieEpisode]]:
        return movie, []

    async def _fill(self, movie: Movie) -> tuple[Movie, list[MovieEpisode]]:
        async with self.session.get(
            url=movie.url,
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            }
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            html = await resp.text()

        soup = bs4.BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("div.inner-page__title h1")
        description_el = soup.select_one("div.inner-page__text[itemprop='description']")
        poster_el = soup.select_one("div.inner-page__img img")

        movie.fill_title = title_el.get_text(strip=True)
        movie.fill_description = description_el.get_text()
        movie.fill_poster = "https://yummyanime.tv" + poster_el["src"]

        external_id = int(movie.external_id.split("-")[1])

        movie.meta.update({"player_urls": []})

        """if "alloha-player" in html:
            return await self._fill_alohaplayer(movie, external_id)

        el"""

        if "xfplayer" in html:
            try:
                _, episodes_ukr = await self._fill_xfplayer_ukranian(movie, external_id)

            except Exception as err:
                logger.exception(err)
                episodes_ukr = []

            try:
                _, episodes_rus = await self._fill_xfplayer_russian(movie, external_id)

            except Exception as err:
                logger.exception(err)
                episodes_rus = []

            return movie, [*episodes_rus, *episodes_ukr]

        else:
            return await self._fill_kodikplayer(movie, external_id)

    async def _fill_episode_thealloha(self, episode: MovieEpisode, player_data: dict) -> MovieEpisode:
        async def find_stream(browser: Browser):
            statuses = {
                "is_found_stream": False,
                "is_found_socket": False,
            }

            async def catch_m3u8(route):
                if "m3u8" in route.request.url and not statuses['is_found_stream']:
                    episode.stream = route.request.url
                    episode.meta["stream_headers"] = route.request.headers
                    statuses["is_found_stream"] = True

                return await route.continue_()

            def catch_socket(msg):
                if "ALLOHASOCKET " in msg.text and not statuses['is_found_socket']:
                    url = msg.text.replace("ALLOHASOCKET ", "")
                    episode.meta["socket"] = url
                    statuses["is_found_socket"] = True

            season_i = episode.season
            episode_i = episode.episode
            episode_id = episode.meta['id']
            id_file = '"' + episode.meta['id_file'] + '"' if episode.meta['id_file'] else "null"
            translation = '"' + episode.meta['translation'] + '"'
            id_translation = episode.meta['id_translation']
            quality = '"' + episode.meta['quality'] + '"'
            id_quality = episode.meta['id_quality']

            await browser.context.add_init_script(f"""
            (() => {{
                const originalParse = JSON.parse;

                JSON.parse = function(str) {{
                    const data = originalParse(str);
                    if (data && data.active && data.active.seasons) {{
                        data.active.id = {episode_id};
                        data.active.seasons = {season_i};
                        data.active.episode = {episode_i};
                        data.active.id_file = {id_file};
                        data.active.translation = {translation};
                        data.active.id_translation = {id_translation};
                        data.active.quality = {quality};
                        data.active.id_quality = {id_quality};
                    }} else if (data && data.hlsSource){{
                        console.log(data);
                    }}
                    return data;
                }};
            }})();
            """)

            await browser.context.add_init_script(r"""
            (function() {
                try {
                    const OriginalWS = window.WebSocket || self.WebSocket;
                    if (!OriginalWS) return;
            
                    const WSProxy = new Proxy(OriginalWS, {
                        construct(target, args) {
                            const url = args[0];
                            if (url.includes('absciss.thealloha.club/ws/?sid=')) {
                                console.error('ALLOHASOCKET', url);
                                return;
                            }
                            return new target(...args);
                        }
                    });
            
                    window.WebSocket = WSProxy;
                    if (typeof self !== 'undefined') {
                        self.WebSocket = WSProxy;
                    }
            
                    let hiddenFactory;
                    Object.defineProperty(window, '__ws_factory', {
                        get: function() { return hiddenFactory || ((u) => new WSProxy(u)); },
                        set: function(v) { hiddenFactory = v; },
                        configurable: true
                    });
                } catch (e) {
                }
            })();
            """)

            browser.context.on("console", catch_socket)
            await browser.page.route("**/*.m3u8", catch_m3u8)

            await browser.page.goto(episode.movie.url)

            time_start = time.time()

            while False in list(statuses.values()):
                if time.time() - time_start > 10:
                    logger.exception("Timeout waiting for stream from alohaplyer")
                    return False

                await asyncio.sleep(1)

            return True

        is_ok = await browser_ins.execute(find_stream)

        if not is_ok:
            return episode

        socket = Socket(
            episode_id=episode.id,
            url=episode.meta["socket"],
            is_active=True,
            headers={},
            data={}
        )
        await sync_to_async(socket.save)()

        return episode

    async def _fill_episode_ashdi(self, episode: MovieEpisode, player_data: dict) -> MovieEpisode:
        episode.stream = episode.meta["file"]
        episode.meta["stream_headers"] = {
            "user-agent": self.user_agent,
            **self.default_get_headers
        }
        return episode

    async def _fill_episode_gencit(self, episode: MovieEpisode, player_data: dict) -> MovieEpisode:
        external_id = player_data["url"].split("?")[0].split("/")[-1]

        async with self.session.get(
            url=f"https://opravar.online/bil/{external_id}",
            headers={
                "user-agent": self.user_agent,
                **self.default_get_headers
            },
            params={
                "season": episode.season,
                "episode": episode.episode,
                "voice": episode.translation.meta["id"],
                "trbut": 0,
                "ref": "https://yummyanime.tv",
            },
            allow_redirects=True
        ) as resp:
            self.logger.info(f"{self.__class__.__name__}:get - {resp}")

            html = await resp.text()

        soup = bs4.BeautifulSoup(html, "html.parser")

        player_el = soup.select_one(f"#videoplayer{external_id}")
        if not player_el:
            return episode

        data = json.loads(player_el.get("data-config"))
        episode.stream = data.get("hls")

        return episode

    async def _fill_episode(self, episode: MovieEpisode) -> MovieEpisode:
        target_data = {
            "url": "",
            "translations": []
        }

        for player_data in episode.movie.meta.get("player_urls", []):
            if episode.translation.external_id in player_data["translations"]:
                target_data = player_data

        """if "thealloha.club" in target_data["url"]:
            return await self._fill_episode_thealloha(episode, target_data)

        el"""

        if "ashdi.vip" in target_data["url"]:
            return await self._fill_episode_ashdi(episode, target_data)

        elif "gencit.info" in target_data["url"]:
            return await self._fill_episode_gencit(episode, target_data)

        return episode
