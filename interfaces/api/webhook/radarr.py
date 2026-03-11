import logging

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

from service.movie_downloaded import movie_downloaded

router = APIRouter(prefix="/radarr")
logger = logging.getLogger(__name__)


class RadarrMovie(BaseModel):
    id: int


class RadarrWebhook(BaseModel):
    eventType: str
    movie: RadarrMovie | None = None


@router.post("", status_code=status.HTTP_200_OK)
async def radarr_webhook(request: Request, payload: RadarrWebhook):
    raw_body = await request.body()
    logger.info("Radarr webhook received: %s", raw_body.decode())

    if payload.eventType == "Test":
        logger.info("Received Radarr test webhook")
        return {"result": "success"}
    if payload.eventType == "Download":
        if payload.movie is None:
            raise ValueError("Missing movie in payload")
        await movie_downloaded(payload.movie.id)
    else:
        logger.warning("Received Radarr webhook event type %s", payload.eventType)
        raise ValueError("Invalid event type")
    return {"result": "success"}
