import logging
from pathlib import Path

from domain.constants import MediaType
from interfaces.transcoder import Video

logger = logging.getLogger(__name__)


def transcode_file(path: Path, media_type: MediaType | None = None) -> None:
    # TODO: This should be refactored so that:
    #  - FFMPEG, FFPROBE and File Operations should be interfaces
    #  - FFMPEG settings should be domain functions
    Video.transcode_from_path(str(path), video_type=media_type)
