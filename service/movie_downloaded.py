import logging
from pathlib import Path


from service.enqueue_transcode import enqueue_transcode


logger = logging.getLogger(__name__)


async def movie_downloaded(movie_path: Path) -> None:
    logger.info(f"Received download notification for Radarr movie {movie_path}")
    enqueue_transcode(movie_path)
