import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func as sqlfunc, select

from app.api.deps import AdminUser, CurrentUser, SessionDep
from app.models.donation import DonationRecord
from app.schemas.donation import DonationCreate, DonationResponse, DonationStatsResponse

router = APIRouter(prefix="/donations", tags=["donations"])


def _generate_receipt() -> str:
    short = uuid.uuid4().hex[:8].upper()
    return f"LAAP-{short}"


@router.post("/", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def record_donation(
    data: DonationCreate,
    session: SessionDep,
    admin: AdminUser,
) -> DonationRecord:
    record = DonationRecord(
        donor_name=data.donor_name,
        donor_email=data.donor_email,
        donor_phone=data.donor_phone,
        amount_inr=data.amount_inr,
        purpose=data.purpose,
        payment_mode=data.payment_mode,
        receipt_number=_generate_receipt(),
        campaign_id=data.campaign_id,
        recorded_by=admin.id,
        date=data.date,
        notes=data.notes,
    )
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record


@router.get("/", response_model=list[DonationResponse])
async def list_donations(
    session: SessionDep,
    admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
) -> list[DonationRecord]:
    result = await session.execute(
        select(DonationRecord)
        .order_by(DonationRecord.date.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/stats", response_model=DonationStatsResponse)
async def donation_stats(session: SessionDep) -> DonationStatsResponse:
    total = await session.scalar(
        select(sqlfunc.coalesce(sqlfunc.sum(DonationRecord.amount_inr), 0))
    )
    count = await session.scalar(select(sqlfunc.count(DonationRecord.id)))
    return DonationStatsResponse(
        total_amount_inr=total or 0,
        donation_count=count or 0,
    )


@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(
    donation_id: uuid.UUID,
    session: SessionDep,
) -> DonationRecord:
    result = await session.execute(
        select(DonationRecord).where(DonationRecord.id == donation_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    return record
