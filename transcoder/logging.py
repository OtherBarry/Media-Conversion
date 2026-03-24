import logging


LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s"
    " - trace_id=%(otelTraceID)s span_id=%(otelSpanID)s"
    " - %(message)s"
)


def configure_logging() -> None:
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
