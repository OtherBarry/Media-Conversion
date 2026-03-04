from pathlib import Path

from domain.constants import MediaType
from interfaces.cli.convert_directory import convert_directory

MEDIA_LIBRARIES = {
    MediaType.TV: Path("/data/media/TV Shows/"),
    MediaType.MOVIE: Path("/data/media/Movies/"),
    MediaType.ANIMATION: Path("/data/media/Animated TV Shows/"),
}


def convert_all() -> None:
    for media_type, media_dir in MEDIA_LIBRARIES.items():
        convert_directory(media_dir, media_type)
