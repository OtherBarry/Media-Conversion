from contextlib import asynccontextmanager

from fastapi import FastAPI
from interfaces.api.webhook import router as webhook_router
from transcoder.events import on_startup, on_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    on_startup()
    yield
    on_shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Transcoder API", lifespan=lifespan)
    app.include_router(webhook_router)
    return app
