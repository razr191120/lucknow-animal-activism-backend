import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func as sqlfunc

from app.api.deps import CurrentUser, SessionDep
from app.models.user import User
from app.models.volunteer import Volunteer, VolunteerActivity
from app.schemas.volunteer import (
    ActivityCreate,
    ActivityResponse,
    LeaderboardEntry,
    VolunteerCreate,
    VolunteerResponse,
    VolunteerUpdate,
)

router = APIRouter(prefix="/volunteers", tags=["volunteers"])

BADGE_THRESHOLDS = [(100, "gold"), (50, "silver"), (10, "bronze")]


def _compute_badge(hours: float) -> str:
    for threshold, badge in BADGE_THRESHOLDS:
        if hours >= threshold:
            return badge
    return "none"


async def _enrich(vol: Volunteer, session: SessionDep) -> VolunteerResponse:
    user = await session.get(User, vol.user_id)
    return VolunteerResponse(
        id=vol.id,
        user_id=vol.user_id,
        full_name=user.full_name if user else None,
        email=user.email if user else None,
        phone=vol.phone,
        skills=vol.skills,
        availability=vol.availability,
        area=vol.area,
        status=vol.status,
        total_hours=vol.total_hours,
        badge=vol.badge,
        joined_at=vol.joined_at,
    )


@router.post("/signup", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: VolunteerCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> VolunteerResponse:
    existing = await session.execute(
        select(Volunteer).where(Volunteer.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already registered as volunteer")

    vol = Volunteer(
        user_id=current_user.id,
        phone=data.phone,
        skills=data.skills,
        availability=data.availability,
        area=data.area,
    )
    session.add(vol)
    await session.flush()
    await session.refresh(vol)
    return await _enrich(vol, session)


@router.get("/me", response_model=VolunteerResponse)
async def get_my_profile(
    session: SessionDep,
    current_user: CurrentUser,
) -> VolunteerResponse:
    result = await session.execute(
        select(Volunteer).where(Volunteer.user_id == current_user.id)
    )
    vol = result.scalar_one_or_none()
    if vol is None:
        raise HTTPException(status_code=404, detail="Not registered as volunteer")
    return await _enrich(vol, session)


@router.patch("/me", response_model=VolunteerResponse)
async def update_my_profile(
    data: VolunteerUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> VolunteerResponse:
    result = await session.execute(
        select(Volunteer).where(Volunteer.user_id == current_user.id)
    )
    vol = result.scalar_one_or_none()
    if vol is None:
        raise HTTPException(status_code=404, detail="Not registered as volunteer")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(vol, k, v)
    await session.flush()
    await session.refresh(vol)
    return await _enrich(vol, session)


@router.get("/", response_model=list[VolunteerResponse])
async def list_volunteers(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> list[VolunteerResponse]:
    result = await session.execute(
        select(Volunteer)
        .order_by(Volunteer.total_hours.desc())
        .offset(skip)
        .limit(limit)
    )
    return [await _enrich(v, session) for v in result.scalars().all()]


@router.post("/activity", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def log_activity(
    data: ActivityCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> VolunteerActivity:
    result = await session.execute(
        select(Volunteer).where(Volunteer.user_id == current_user.id)
    )
    vol = result.scalar_one_or_none()
    if vol is None:
        raise HTTPException(status_code=404, detail="Not registered as volunteer")

    activity = VolunteerActivity(
        volunteer_id=vol.id,
        activity_type=data.activity_type,
        entity_id=data.entity_id,
        description=data.description,
        hours=data.hours,
        date=data.date,
    )
    session.add(activity)

    vol.total_hours += data.hours
    vol.badge = _compute_badge(vol.total_hours)

    await session.flush()
    await session.refresh(activity)
    return activity


@router.get("/activity", response_model=list[ActivityResponse])
async def my_activity(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> list[VolunteerActivity]:
    vol_result = await session.execute(
        select(Volunteer).where(Volunteer.user_id == current_user.id)
    )
    vol = vol_result.scalar_one_or_none()
    if vol is None:
        raise HTTPException(status_code=404, detail="Not registered as volunteer")

    result = await session.execute(
        select(VolunteerActivity)
        .where(VolunteerActivity.volunteer_id == vol.id)
        .order_by(VolunteerActivity.date.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(
    session: SessionDep,
    limit: int = 50,
) -> list[LeaderboardEntry]:
    result = await session.execute(
        select(Volunteer, User.full_name)
        .join(User, User.id == Volunteer.user_id)
        .where(Volunteer.status == "active")
        .order_by(Volunteer.total_hours.desc())
        .limit(limit)
    )
    return [
        LeaderboardEntry(
            volunteer_id=vol.id,
            full_name=name,
            total_hours=vol.total_hours,
            badge=vol.badge,
            area=vol.area,
        )
        for vol, name in result.all()
    ]
