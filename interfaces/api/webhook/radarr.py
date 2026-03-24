import logging
from pathlib import Path

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

from service.movie_downloaded import movie_downloaded

router = APIRouter(prefix="/radarr")
logger = logging.getLogger(__name__)


class RadarrMovie(BaseModel):
    path: Path


class RadarrWebhook(BaseModel):
    eventType: str
    movieFile: RadarrMovie | None = None


@router.post("", status_code=status.HTTP_200_OK)
async def radarr_webhook(request: Request, payload: RadarrWebhook) -> dict[str, str]:
    logger.info("Radarr webhook received: %s", await request.json())

    if payload.eventType == "Test":
        logger.info("Received Radarr test webhook")
        return {"result": "success"}
    if payload.eventType == "Download":
        if payload.movieFile is None:
            raise ValueError("Missing movie in payload")
        await movie_downloaded(payload.movieFile.path)
    else:
        logger.warning("Received Radarr webhook event type %s", payload.eventType)
        raise ValueError("Invalid event type")
    return {"result": "success"}
