from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import distributions, drives, geocoding, stats


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Lucknow Water Bowl Distribution API",
    description="Backend for managing water bowl distribution drives for animals in Lucknow, India",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

API_PREFIX = "/api/v1"

app.include_router(drives.router, prefix=API_PREFIX)
app.include_router(distributions.router, prefix=API_PREFIX)
app.include_router(geocoding.router, prefix=API_PREFIX)
app.include_router(stats.router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
