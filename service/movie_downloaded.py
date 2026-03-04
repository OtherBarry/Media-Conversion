import logging

from dependency_injector.wiring import inject, Provide

from interfaces.radarr import RadarrClient
from service.enqueue_transcode import enqueue_transcode
from transcoder.dependencies import Dependencies


logger = logging.getLogger(__name__)


@inject
async def movie_downloaded(
    movie_id: int,
    radarr_client: RadarrClient = Provide[Dependencies.radarr_client],
) -> None:
    logger.info(f"Received download notification for Radarr movie {movie_id}")
    movie_path = await radarr_client.get_movie_path(movie_id)
    enqueue_transcode(movie_path)
