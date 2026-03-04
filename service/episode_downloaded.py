import logging

from dependency_injector.wiring import inject, Provide

from interfaces.sonarr import SonarrClient
from service.enqueue_transcode import enqueue_transcode
from transcoder.dependencies import Dependencies

logger = logging.getLogger(__name__)


@inject
async def episode_downloaded(
    episode_id: int,
    sonarr_client: SonarrClient = Provide[Dependencies.sonarr_client],
) -> None:
    logger.info(f"Received download notification for Sonarr episode {episode_id}")
    episode_path = await sonarr_client.get_episode_path(episode_id)
    enqueue_transcode(episode_path)
