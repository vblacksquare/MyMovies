
import asyncio
import logging
from itertools import chain

from . import Parser
from ...models import Source, Movie, MovieEpisode
from .browser import browser_ins


logger = logging.getLogger("Movies")
TIMEOUT = 5


async def fill(movie: Movie) -> tuple[Movie, list[MovieEpisode]]:
    obj = None
    for cls in Parser.__subclasses__():
        if cls.source == movie.source:
            obj = cls()
            break

    episodes = []
    try:
        movies, episodes = await asyncio.wait_for(obj.fill(movie), TIMEOUT)

    except Exception as err:
        logging.exception(err)
        if browser_ins._lock.locked():
            browser_ins._lock.release()

    await obj.close()

    return movie, episodes


async def fill_episode(episode: MovieEpisode) -> MovieEpisode:
    obj = None
    for cls in Parser.__subclasses__():
        if cls.source == episode.movie.source:
            obj = cls()
            break

    try:
        episode = await asyncio.wait_for(obj.fill_episode(episode), TIMEOUT)

    except Exception as err:
        logging.exception(err)
        if browser_ins._lock.locked():
            browser_ins._lock.release()

    await obj.close()

    return episode


async def search(query: str, sources: list[Source]) -> list[Movie]:
    query = query.strip()
    if query in ["", " "]:
        return []

    objs = [
        cls()
        for cls in Parser.__subclasses__() if cls.source in sources
    ]

    episodes = []
    try:
        for obj in objs:
            episodes += await asyncio.wait_for(obj.search(query), TIMEOUT)

    except Exception as err:
        logging.exception(err)
        if browser_ins._lock.locked():
            browser_ins._lock.release()

    await asyncio.gather(*[
        obj.close()
        for obj in objs
    ])

    return episodes
