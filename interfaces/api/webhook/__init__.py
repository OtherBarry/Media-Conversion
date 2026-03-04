from fastapi import APIRouter

from .radarr import router as radarr_router
from .sonarr import router as sonarr_router

router = APIRouter(prefix="/webhook", tags=["webhook"])
router.include_router(radarr_router)
router.include_router(sonarr_router)
