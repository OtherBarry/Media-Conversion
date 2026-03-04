import logging
from pathlib import Path

from dependency_injector.wiring import inject, Provide

from domain.constants import MediaType
from interfaces.rq import RQClient
from transcoder.dependencies import Dependencies

logger = logging.getLogger(__name__)


@inject
def enqueue_transcode(
    video_path: Path,
    media_type: MediaType | None = None,
    rq_client: RQClient = Provide[Dependencies.rq_client],
) -> None:
    logger.info(f"Enqueueing transcode for {video_path}")
    rq_client.enqueue_transcode(video_path, media_type)
