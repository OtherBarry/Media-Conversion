from pathlib import Path

from domain.constants import MediaType
from service.enqueue_transcode import enqueue_transcode


def convert(file_path: Path, media_type: MediaType | None = None) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    enqueue_transcode(file_path, media_type)
