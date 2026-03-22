
from asgiref.sync import sync_to_async

import logging
import aiohttp
import asyncio
from abc import abstractmethod, ABC

from ...models import SourceSession, Movie, MovieEpisode


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(asctime)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("movies.log")
    ]
)


logger = logging.getLogger("movies")
sem = asyncio.Semaphore(1)


class Parser(ABC):
    source = None
    user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36")
    default_get_headers = {
        "accept": "text/html,application/xhtml+xml,"
                  "application/xml;q=0.9,image/avif,"
                  "image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
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
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"
    }
    logger = logger

    def __init__(self):
        self.session: aiohttp.ClientSession = None
        self.source_session: SourceSession = None

    async def close(self):
        if self.session:
            await self.session.close()

    @abstractmethod
    async def auth(self) -> tuple[aiohttp.ClientSession, dict]:
        return [aiohttp.ClientSession(), {}]

    @abstractmethod
    async def _search(self, query: str) -> list[Movie]:
        pass

    @abstractmethod
    async def _fill(self, movie: Movie) -> tuple[Movie, list[MovieEpisode]]:
        pass

    @abstractmethod
    async def _fill_episode(self, movie: Movie) -> MovieEpisode:
        pass

    async def get_session(self) -> tuple[aiohttp.ClientSession, SourceSession]:
        """if self.source_session is None:
            source_session = await sync_to_async(SourceSession.objects.filter(source=self.source).first)()
        else:"""
        source_session = self.source_session

        if self.session is None:
            if source_session is None:
                session, meta = await self.auth()
                source_session = SourceSession(
                    cookies={
                        cookie.key: cookie.value
                        for cookie in session.cookie_jar
                    },
                    meta=meta,
                    source=self.source
                )
                await sync_to_async(source_session.save)()

            else:
                session = aiohttp.ClientSession(
                    cookies=source_session.cookies
                )
                logger.info(f"{self.__class__.__name__}:auth - from memmory")

            return session, source_session

        return self.session, self.source_session

    async def prepare(self):
        self.session, self.source_session = await self.get_session()

        for key in self.source_session.cookies:
            value = self.source_session.cookies[key]
            logger.info(f"{self.__class__.__name__}:auth {key} = {value}")

        for key in self.source_session.meta:
            value = self.source_session.meta[key]
            logger.info(f"{self.__class__.__name__}:auth {key} = {value}")

    async def search(self, query: str) -> list[Movie]:
        try:
            await self.prepare()
            return await self._search(query)

        except Exception as err:
            logger.exception(err)

            return []

    async def fill(self, movie: Movie) -> tuple[Movie, list[MovieEpisode]]:
        try:
            await self.prepare()
            return await self._fill(movie)

        except Exception as err:
            logger.exception(err)

            return movie, []

    async def fill_episode(self, episode: MovieEpisode) -> MovieEpisode:
        try:
            await self.prepare()
            episode = await self._fill_episode(episode)
            self.logger.info(f"{self.__class__.__name__}:fill_episode - {episode.stream}")

            return episode

        except Exception as err:
            logger.exception(err)

            return episode
