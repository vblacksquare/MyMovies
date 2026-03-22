
import asyncio
from itertools import chain

from . import Parser
from ...models import Source, Movie, MovieEpisode


async def fill(movie: Movie) -> tuple[Movie, list[MovieEpisode]]:
    obj = None
    for cls in Parser.__subclasses__():
        if cls.source == movie.source:
            obj = cls()
            break

    movie, episodes = await obj.fill(movie)
    await obj.close()

    return movie, episodes


async def fill_episode(episode: MovieEpisode) -> MovieEpisode:
    obj = None
    for cls in Parser.__subclasses__():
        if cls.source == episode.movie.source:
            obj = cls()
            break

    episode = await obj.fill_episode(episode)
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

    groups = await asyncio.gather(*[
        obj.search(query)
        for obj in objs
    ])
    await asyncio.gather(*[
        obj.close()
        for obj in objs
    ])

    return list(chain(*groups))
