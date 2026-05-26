import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import alerts, status, ticker_trends
from app.trend_worker import trend_loop
from app.worker import poll_loop

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    tasks = [asyncio.create_task(poll_loop())]
    if settings.apewisdom_enabled:
        tasks.append(asyncio.create_task(trend_loop()))
    yield
    for task in tasks:
        task.cancel()
    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Gold/Silver Ratio Alerts",
    description="Watch the gold/silver ratio and get Discord alerts on threshold crosses.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)
app.include_router(alerts.router)
app.include_router(ticker_trends.router)
