import logging
import logging.config

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.database import init_db
from app.api.routes import router

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database tables")
    await init_db()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Tasks & Orders API",
    description="Async REST API backed by RabbitMQ and PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "Tasks & Orders API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "tasks": "/tasks",
            "orders": "/orders",
        },
    }
