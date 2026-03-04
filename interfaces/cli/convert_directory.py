from pathlib import Path

from domain.constants import MediaType
from service.enqueue_transcode import enqueue_transcode


FILE_EXTENSIONS = (
    "mkv",
    "m4v",
    "avi",
    "wmv",
    "mov",
    "mp4",
)
TYPES = ["**/*." + x for x in FILE_EXTENSIONS]


def convert_directory(directory: Path, media_type: MediaType) -> None:
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    for file_type in TYPES:
        for file in directory.glob(file_type):
            enqueue_transcode(file, media_type=media_type)
