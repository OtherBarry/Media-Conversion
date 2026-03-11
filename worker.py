"""Custom RQ worker script.

Preloads logging, OpenTelemetry, and dependency injection *before* the
worker's fetch-fork-execute loop so every forked job process inherits
the fully-configured environment without paying the setup cost each time.
"""

from redis import Redis
from rq import Worker

from transcoder.events import on_startup, on_shutdown
from transcoder.settings import settings

# Preload: configure logging, OpenTelemetry, and DI
on_startup()

# Preload heavy job dependencies so they are already imported before fork
import interfaces.transcoder  # noqa: E402, F401
import service.transcode  # noqa: E402, F401

w = Worker(
    ["default"],
    connection=Redis(host=settings.redis_host, port=settings.redis_port),
)
w.work()

on_shutdown()
