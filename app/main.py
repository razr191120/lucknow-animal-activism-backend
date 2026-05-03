import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin, attachments, auth, distributions, drives, geocoding, stats

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lucknow Water Bowl Distribution API",
    description="Backend for managing water bowl distribution drives for animals in Lucknow, India",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(drives.router, prefix=API_PREFIX)
app.include_router(distributions.router, prefix=API_PREFIX)
app.include_router(geocoding.router, prefix=API_PREFIX)
app.include_router(stats.router, prefix=API_PREFIX)
app.include_router(attachments.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
