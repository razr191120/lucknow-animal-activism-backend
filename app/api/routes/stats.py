from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models.distribution import Distribution
from app.models.donation import DonationRecord
from app.models.drive import Drive
from app.models.laap import LaapAdoptionRequest, LaapRescueRequest
from app.models.volunteer import Volunteer
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

    total_rescues = await session.scalar(select(func.count(LaapRescueRequest.id)))
    open_rescues = await session.scalar(
        select(func.count(LaapRescueRequest.id)).where(LaapRescueRequest.status == "open")
    )
    resolved_rescues = await session.scalar(
        select(func.count(LaapRescueRequest.id)).where(LaapRescueRequest.status == "resolved")
    )

    total_adoptions = await session.scalar(select(func.count(LaapAdoptionRequest.id)))
    open_adoptions = await session.scalar(
        select(func.count(LaapAdoptionRequest.id)).where(LaapAdoptionRequest.status == "open")
    )
    fulfilled_adoptions = await session.scalar(
        select(func.count(LaapAdoptionRequest.id)).where(
            LaapAdoptionRequest.status == "fulfilled"
        )
    )

    total_donations_inr = await session.scalar(
        select(func.coalesce(func.sum(DonationRecord.amount_inr), 0))
    )
    donation_count = await session.scalar(select(func.count(DonationRecord.id)))

    total_volunteers = await session.scalar(select(func.count(Volunteer.id)))
    active_volunteers = await session.scalar(
        select(func.count(Volunteer.id)).where(Volunteer.status == "active")
    )

    return StatsResponse(
        total_distributions=total_dist or 0,
        total_drives=total_drives or 0,
        drives_completed=completed or 0,
        drives_planned=planned or 0,
        unique_addresses=unique_addr or 0,
        total_rescues=total_rescues or 0,
        open_rescues=open_rescues or 0,
        resolved_rescues=resolved_rescues or 0,
        total_adoptions=total_adoptions or 0,
        open_adoptions=open_adoptions or 0,
        fulfilled_adoptions=fulfilled_adoptions or 0,
        total_donations_inr=float(total_donations_inr or 0),
        donation_count=donation_count or 0,
        total_volunteers=total_volunteers or 0,
        active_volunteers=active_volunteers or 0,
    )
