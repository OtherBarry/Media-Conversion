import logging
from logging.handlers import WatchedFileHandler

from transcoder.settings import settings


def configure_logging():
    log_handler = WatchedFileHandler(settings.log_path)
    formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] %(message)s", "%b %d %H:%M:%S"
    )
    log_handler.setFormatter(formatter)
