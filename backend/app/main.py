import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import alerts, status
from app.worker import poll_loop

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Gold/Silver Ratio Alerts",
    description="Watch the gold/silver ratio and get Discord alerts on threshold crosses.",
    lifespan=lifespan,
)

app.include_router(status.router)
app.include_router(alerts.router)
