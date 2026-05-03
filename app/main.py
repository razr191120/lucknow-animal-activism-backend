from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, attachments, auth, distributions, drives, geocoding, stats

app = FastAPI(
    title="Lucknow Water Bowl Distribution API",
    description="Backend for managing water bowl distribution drives for animals in Lucknow, India",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
