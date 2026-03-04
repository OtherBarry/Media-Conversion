from pathlib import Path

from redis import Redis
from rq import Queue

from domain.constants import MediaType


class RQClient:
    def __init__(self, redis_url: str, redis_port: int, timeout: int) -> None:
        redis_connection = Redis(host=redis_url, port=redis_port)
        self._queue = Queue(connection=redis_connection, default_timeout=timeout)

    def enqueue_transcode(
        self, path: Path, media_type: MediaType | None = None
    ) -> None:
        self._queue.enqueue(
            "service.transcode.transcode_file", path=path, media_type=media_type
        )
