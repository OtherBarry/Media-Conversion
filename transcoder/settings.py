from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Transcode
    transcode_timeout: int = 20000
    puid: int = 13015
    pgid: int = 13000

    # Logs
    log_path: str = "./transcoder-server.log"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # Radarr
    radarr_base_url: str = "http://radarr:7878"
    radarr_api_key: SecretStr

    # Sonarr
    sonarr_base_url: str = "http://sonarr:8989"
    sonarr_api_key: SecretStr


settings = Settings()
