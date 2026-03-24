import logging

from opentelemetry import metrics, trace

from transcoder.dependencies import wire_dependencies
from transcoder.logging import configure_logging
from transcoder.observability import configure_telemetry

logger = logging.getLogger(__name__)


def on_startup() -> None:
    configure_logging()
    configure_telemetry()
    wire_dependencies()
    logger.info("Started up")


def on_shutdown() -> None:
    logger.info("Shutting down")
    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, "shutdown"):
        tracer_provider.shutdown()
    meter_provider = metrics.get_meter_provider()
    if hasattr(meter_provider, "shutdown"):
        meter_provider.shutdown()
