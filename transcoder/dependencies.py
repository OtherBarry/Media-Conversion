from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from interfaces.rq import RQClient
from transcoder.settings import settings


class Dependencies(DeclarativeContainer):
    settings = providers.Configuration(pydantic_settings=[settings])

    rq_client = providers.Singleton(
        RQClient,
        redis_url=settings.redis_host,
        redis_port=settings.redis_port,
        timeout=settings.transcode_timeout,
    )


def wire_dependencies() -> None:
    dependencies = Dependencies()
    dependencies.wire(packages=["service"])
