import logging

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from transcoder.settings import settings

logger = logging.getLogger(__name__)


def _build_resource() -> Resource:
    return Resource.create(
        {
            "service.name": settings.otel_service_name,
        }
    )


def configure_telemetry() -> None:
    """Configure OpenTelemetry tracing, metrics, and auto-instrumentation."""
    resource = _build_resource()

    # --- Traces ---
    trace_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # --- Metrics ---
    metric_exporter = OTLPMetricExporter(endpoint=settings.otel_exporter_endpoint)
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter, export_interval_millis=30_000
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # --- Auto-instrumentation ---
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=True)

    logger.info(
        "OpenTelemetry configured (endpoint=%s)", settings.otel_exporter_endpoint
    )


def instrument_fastapi(app: FastAPI) -> None:
    """Instrument a FastAPI app instance. Call after app creation."""
    FastAPIInstrumentor.instrument_app(app)
