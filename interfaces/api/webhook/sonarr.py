import logging

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

from service.episode_downloaded import episode_downloaded

router = APIRouter(prefix="/sonarr")
logger = logging.getLogger(__name__)


class SonarrEpisode(BaseModel):
    id: int


class SonarrWebhook(BaseModel):
    eventType: str
    episode: SonarrEpisode | None = None


@router.post("", status_code=status.HTTP_200_OK)
async def sonarr_webhook(request: Request, payload: SonarrWebhook):
    logger.info("Radarr webhook received: %s", await request.json())

    if payload.eventType == "Test":
        logger.info("Received Sonarr test webhook")
        return {"result": "success"}
    if payload.eventType == "Download":
        if payload.episode is None:
            raise ValueError("Missing episode in payload")
        await episode_downloaded(payload.episode.id)
    else:
        logger.warning("Received Sonarr webhook event type %s", payload.eventType)
        raise ValueError("Invalid event type")
    return {"result": "success"}
