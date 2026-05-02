from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models.distribution import Distribution
from app.models.drive import Drive
from app.schemas.distribution import StatsResponse

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(session: SessionDep) -> StatsResponse:
    total_dist = await session.scalar(select(func.count(Distribution.id)))
    total_drives = await session.scalar(select(func.count(Drive.id)))
    completed = await session.scalar(
        select(func.count(Drive.id)).where(Drive.status == "completed")
    )
    planned = await session.scalar(
        select(func.count(Drive.id)).where(Drive.status == "planned")
    )
    unique_addr = await session.scalar(
        select(func.count(func.distinct(Distribution.address))).where(
            Distribution.address.is_not(None)
        )
    )

    return StatsResponse(
        total_distributions=total_dist or 0,
        total_drives=total_drives or 0,
        drives_completed=completed or 0,
        drives_planned=planned or 0,
        unique_addresses=unique_addr or 0,
    )
