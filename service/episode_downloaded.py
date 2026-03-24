import logging
from pathlib import Path

from service.enqueue_transcode import enqueue_transcode

logger = logging.getLogger(__name__)


async def episode_downloaded(episode_path: Path) -> None:
    logger.info(f"Received download notification for Sonarr episode {episode_path}")
    enqueue_transcode(episode_path)
