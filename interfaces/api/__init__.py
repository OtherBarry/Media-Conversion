from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from interfaces.api.webhook import router as webhook_router
from transcoder.events import on_startup, on_shutdown
from transcoder.observability import instrument_fastapi


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    on_startup()
    yield
    on_shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Transcoder API", lifespan=lifespan)
    app.include_router(webhook_router)
    instrument_fastapi(app)
    return app
