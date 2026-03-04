import logging

from transcoder.dependencies import wire_dependencies
from transcoder.logging import configure_logging

logger = logging.getLogger(__name__)


def on_startup():
    configure_logging()
    wire_dependencies()
    logger.info("Started up")


def on_shutdown():
    logger.info("Shutting down")
