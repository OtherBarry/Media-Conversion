from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Transcode
    transcode_timeout: int = 20000
    puid: int = 13015
    pgid: int = 13000

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # OpenTelemetry
    otel_service_name: str = "transcoder"
    otel_exporter_endpoint: str = "http://alloy:4318"


settings = Settings()
