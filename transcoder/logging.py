import logging
import sys
from logging.handlers import WatchedFileHandler

from transcoder.settings import settings


def configure_logging() -> None:
    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        settings.log_path,
        when="D",
        interval=1,
        backupCount=7,
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])
