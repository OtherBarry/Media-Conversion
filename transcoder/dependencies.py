from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from interfaces.radarr import RadarrClient
from interfaces.rq import RQClient
from interfaces.sonarr import SonarrClient
from transcoder.settings import settings


class Dependencies(DeclarativeContainer):
    settings = providers.Configuration(pydantic_settings=[settings])

    rq_client = providers.Singleton(
        RQClient,
        redis_url=settings.redis_host,
        redis_port=settings.redis_port,
        timeout=settings.transcode_timeout,
    )

    radarr_client = providers.Singleton(
        RadarrClient,
        base_url=settings.radarr_base_url,
        api_key=settings.provided["radarr_api_key"].get_secret_value.call(),
    )

    sonarr_client = providers.Singleton(
        SonarrClient,
        base_url=settings.sonarr_base_url,
        api_key=settings.provided["sonarr_api_key"].get_secret_value.call(),
    )


def wire_dependencies() -> None:
    dependencies = Dependencies()
    dependencies.wire(packages=["service"])
