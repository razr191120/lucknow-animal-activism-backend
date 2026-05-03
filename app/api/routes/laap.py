import uuid
from decimal import Decimal
from typing import Sequence

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.models.attachment import Attachment
from app.models.laap import LaapAdoptionRequest, LaapDonationRequest, LaapRescueRequest
from app.models.user import User
from app.schemas.laap import (
    LaapAdoptionResponse,
    LaapAdoptionUpdate,
    LaapDonationResponse,
    LaapDonationUpdate,
    LaapRescueResponse,
    LaapRescueUpdate,
)
from app.services.blob_storage import blob_storage_service

router = APIRouter(prefix="/laap", tags=["laap"])

ET_ADOPTION = "laap_adoption"
ET_RESCUE = "laap_rescue"
ET_DONATION = "laap_donation"


def _can_edit(user: User, owner_id: uuid.UUID) -> bool:
    return user.role == "admin" or user.id == owner_id


def _gather_files(*files: UploadFile | None) -> list[UploadFile]:
    return [f for f in files if f is not None and f.filename]


async def _photo_urls(
    session: SessionDep, entity_type: str, entity_id: uuid.UUID
) -> list[str]:
    result = await session.execute(
        select(Attachment.blob_url, Attachment.field_name, Attachment.created_at)
        .where(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id,
        )
        .order_by(Attachment.created_at.asc())
    )
    rows = result.all()
    rows.sort(key=lambda r: (r[1] or "", str(r[2])))
    return [r[0] for r in rows]


async def _upload_images(
    session: SessionDep,
    uploads: Sequence[UploadFile],
    entity_type: str,
    entity_id: uuid.UUID,
    uploaded_by: str,
) -> None:
    for idx, upload in enumerate(uploads):
        blob_name, blob_url, size_bytes = await blob_storage_service.upload(upload)
        session.add(
            Attachment(
                blob_name=blob_name,
                blob_url=blob_url,
                original_filename=upload.filename,
                content_type=upload.content_type,
                size_bytes=size_bytes,
                entity_type=entity_type,
                entity_id=entity_id,
                field_name=f"photo_{idx}",
                uploaded_by=uploaded_by,
            )
        )


def _parse_optional_decimal(raw: str | None) -> Decimal | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        return Decimal(raw.strip())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid target_amount_inr",
        ) from e


# ── Adoptions ───────────────────────────────────────────────────────────────


@router.post(
    "/adoptions",
    response_model=LaapAdoptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_adoption(
    session: SessionDep,
    current_user: CurrentUser,
    title: str = Form(...),
    animal_name: str | None = Form(None),
    description: str | None = Form(None),
    contact_phone: str | None = Form(None),
    location_hint: str | None = Form(None),
    image_0: UploadFile | None = File(None),
    image_1: UploadFile | None = File(None),
    image_2: UploadFile | None = File(None),
    image_3: UploadFile | None = File(None),
    image_4: UploadFile | None = File(None),
) -> LaapAdoptionResponse:
    row = LaapAdoptionRequest(
        user_id=current_user.id,
        title=title,
        animal_name=animal_name,
        description=description,
        contact_phone=contact_phone,
        location_hint=location_hint,
        status="open",
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)

    uploads = _gather_files(image_0, image_1, image_2, image_3, image_4)
    if uploads:
        await _upload_images(
            session,
            uploads,
            ET_ADOPTION,
            row.id,
            str(current_user.id),
        )

    await session.flush()
    await session.refresh(row)
    urls = await _photo_urls(session, ET_ADOPTION, row.id)
    return LaapAdoptionResponse(
        id=row.id,
        user_id=row.user_id,
        creator_full_name=current_user.full_name,
        title=row.title,
        animal_name=row.animal_name,
        description=row.description,
        contact_phone=row.contact_phone,
        location_hint=row.location_hint,
        status=row.status,
        photo_urls=urls,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/adoptions", response_model=list[LaapAdoptionResponse])
async def list_adoptions(
    session: SessionDep,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[LaapAdoptionResponse]:
    q = (
        select(LaapAdoptionRequest, User.full_name)
        .join(User, User.id == LaapAdoptionRequest.user_id)
        .order_by(LaapAdoptionRequest.created_at.desc())
    )
    if status_filter:
        q = q.where(LaapAdoptionRequest.status == status_filter)
    else:
        q = q.where(LaapAdoptionRequest.status != "withdrawn")
    result = await session.execute(q.offset(skip).limit(limit))
    out: list[LaapAdoptionResponse] = []
    for row, full_name in result.all():
        urls = await _photo_urls(session, ET_ADOPTION, row.id)
        out.append(
            LaapAdoptionResponse(
                id=row.id,
                user_id=row.user_id,
                creator_full_name=full_name,
                title=row.title,
                animal_name=row.animal_name,
                description=row.description,
                contact_phone=row.contact_phone,
                location_hint=row.location_hint,
                status=row.status,
                photo_urls=urls,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    return out


@router.get("/adoptions/{adoption_id}", response_model=LaapAdoptionResponse)
async def get_adoption(
    adoption_id: uuid.UUID,
    session: SessionDep,
) -> LaapAdoptionResponse:
    result = await session.execute(
        select(LaapAdoptionRequest, User.full_name)
        .join(User, User.id == LaapAdoptionRequest.user_id)
        .where(LaapAdoptionRequest.id == adoption_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Adoption request not found")
    a, full_name = row
    urls = await _photo_urls(session, ET_ADOPTION, a.id)
    return LaapAdoptionResponse(
        id=a.id,
        user_id=a.user_id,
        creator_full_name=full_name,
        title=a.title,
        animal_name=a.animal_name,
        description=a.description,
        contact_phone=a.contact_phone,
        location_hint=a.location_hint,
        status=a.status,
        photo_urls=urls,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.patch("/adoptions/{adoption_id}", response_model=LaapAdoptionResponse)
async def update_adoption(
    adoption_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    body: LaapAdoptionUpdate,
) -> LaapAdoptionResponse:
    result = await session.execute(
        select(LaapAdoptionRequest).where(LaapAdoptionRequest.id == adoption_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Adoption request not found")
    if not _can_edit(current_user, row.user_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await session.flush()
    await session.refresh(row)

    u = await session.execute(select(User.full_name).where(User.id == row.user_id))
    creator = u.scalar_one()
    urls = await _photo_urls(session, ET_ADOPTION, row.id)
    return LaapAdoptionResponse(
        id=row.id,
        user_id=row.user_id,
        creator_full_name=creator,
        title=row.title,
        animal_name=row.animal_name,
        description=row.description,
        contact_phone=row.contact_phone,
        location_hint=row.location_hint,
        status=row.status,
        photo_urls=urls,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ── Rescues ─────────────────────────────────────────────────────────────────


@router.post(
    "/rescues",
    response_model=LaapRescueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rescue(
    session: SessionDep,
    current_user: CurrentUser,
    title: str = Form(...),
    description: str | None = Form(None),
    location_address: str = Form(...),
    contact_phone: str | None = Form(None),
    animal_condition: str | None = Form(None),
    urgency: str = Form("high"),
    image_0: UploadFile | None = File(None),
    image_1: UploadFile | None = File(None),
    image_2: UploadFile | None = File(None),
    image_3: UploadFile | None = File(None),
    image_4: UploadFile | None = File(None),
) -> LaapRescueResponse:
    if urgency not in ("urgent", "high", "medium"):
        raise HTTPException(status_code=400, detail="Invalid urgency")
    row = LaapRescueRequest(
        user_id=current_user.id,
        title=title,
        description=description,
        location_address=location_address,
        contact_phone=contact_phone,
        animal_condition=animal_condition,
        urgency=urgency,
        status="open",
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)

    uploads = _gather_files(image_0, image_1, image_2, image_3, image_4)
    if uploads:
        await _upload_images(
            session, uploads, ET_RESCUE, row.id, str(current_user.id)
        )

    await session.flush()
    await session.refresh(row)
    urls = await _photo_urls(session, ET_RESCUE, row.id)
    return LaapRescueResponse(
        id=row.id,
        user_id=row.user_id,
        creator_full_name=current_user.full_name,
        title=row.title,
        description=row.description,
        location_address=row.location_address,
        contact_phone=row.contact_phone,
        animal_condition=row.animal_condition,
        urgency=row.urgency,
        status=row.status,
        photo_urls=urls,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/rescues", response_model=list[LaapRescueResponse])
async def list_rescues(
    session: SessionDep,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[LaapRescueResponse]:
    q = (
        select(LaapRescueRequest, User.full_name)
        .join(User, User.id == LaapRescueRequest.user_id)
        .order_by(LaapRescueRequest.created_at.desc())
    )
    if status_filter:
        q = q.where(LaapRescueRequest.status == status_filter)
    else:
        q = q.where(LaapRescueRequest.status != "withdrawn")
    result = await session.execute(q.offset(skip).limit(limit))
    out: list[LaapRescueResponse] = []
    for row, full_name in result.all():
        urls = await _photo_urls(session, ET_RESCUE, row.id)
        out.append(
            LaapRescueResponse(
                id=row.id,
                user_id=row.user_id,
                creator_full_name=full_name,
                title=row.title,
                description=row.description,
                location_address=row.location_address,
                contact_phone=row.contact_phone,
                animal_condition=row.animal_condition,
                urgency=row.urgency,
                status=row.status,
                photo_urls=urls,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    return out


@router.get("/rescues/{rescue_id}", response_model=LaapRescueResponse)
async def get_rescue(
    rescue_id: uuid.UUID,
    session: SessionDep,
) -> LaapRescueResponse:
    result = await session.execute(
        select(LaapRescueRequest, User.full_name)
        .join(User, User.id == LaapRescueRequest.user_id)
        .where(LaapRescueRequest.id == rescue_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Rescue request not found")
    r, full_name = row
    urls = await _photo_urls(session, ET_RESCUE, r.id)
    return LaapRescueResponse(
        id=r.id,
        user_id=r.user_id,
        creator_full_name=full_name,
        title=r.title,
        description=r.description,
        location_address=r.location_address,
        contact_phone=r.contact_phone,
        animal_condition=r.animal_condition,
        urgency=r.urgency,
        status=r.status,
        photo_urls=urls,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.patch("/rescues/{rescue_id}", response_model=LaapRescueResponse)
async def update_rescue(
    rescue_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    body: LaapRescueUpdate,
) -> LaapRescueResponse:
    result = await session.execute(
        select(LaapRescueRequest).where(LaapRescueRequest.id == rescue_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Rescue request not found")
    if not _can_edit(current_user, row.user_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await session.flush()
    await session.refresh(row)

    u = await session.execute(select(User.full_name).where(User.id == row.user_id))
    creator = u.scalar_one()
    urls = await _photo_urls(session, ET_RESCUE, row.id)
    return LaapRescueResponse(
        id=row.id,
        user_id=row.user_id,
        creator_full_name=creator,
        title=row.title,
        description=row.description,
        location_address=row.location_address,
        contact_phone=row.contact_phone,
        animal_condition=row.animal_condition,
        urgency=row.urgency,
        status=row.status,
        photo_urls=urls,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ── Donations ───────────────────────────────────────────────────────────────


@router.post(
    "/donations",
    response_model=LaapDonationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation_request(
    session: SessionDep,
    current_user: CurrentUser,
    title: str = Form(...),
    description: str | None = Form(None),
    items_or_need_summary: str | None = Form(None),
    how_to_donate: str | None = Form(None),
    contact_phone: str | None = Form(None),
    upi_id: str | None = Form(None),
    bank_account_hint: str | None = Form(None),
    target_amount_inr: str | None = Form(None),
    image_0: UploadFile | None = File(None),
    image_1: UploadFile | None = File(None),
    image_2: UploadFile | None = File(None),
    image_3: UploadFile | None = File(None),
    image_4: UploadFile | None = File(None),
) -> LaapDonationResponse:
    amt = _parse_optional_decimal(target_amount_inr)
    row = LaapDonationRequest(
        user_id=current_user.id,
        title=title,
        description=description,
        items_or_need_summary=items_or_need_summary,
        how_to_donate=how_to_donate,
        contact_phone=contact_phone,
        upi_id=upi_id,
        bank_account_hint=bank_account_hint,
        target_amount_inr=amt,
        status="open",
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)

    uploads = _gather_files(image_0, image_1, image_2, image_3, image_4)
    if uploads:
        await _upload_images(
            session, uploads, ET_DONATION, row.id, str(current_user.id)
        )

    await session.flush()
    await session.refresh(row)
    urls = await _photo_urls(session, ET_DONATION, row.id)
    return LaapDonationResponse(
        id=row.id,
        user_id=row.user_id,
        creator_full_name=current_user.full_name,
        title=row.title,
        description=row.description,
        items_or_need_summary=row.items_or_need_summary,
        how_to_donate=row.how_to_donate,
        contact_phone=row.contact_phone,
        upi_id=row.upi_id,
        bank_account_hint=row.bank_account_hint,
        target_amount_inr=row.target_amount_inr,
        status=row.status,
        photo_urls=urls,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/donations", response_model=list[LaapDonationResponse])
async def list_donation_requests(
    session: SessionDep,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[LaapDonationResponse]:
    q = (
        select(LaapDonationRequest, User.full_name)
        .join(User, User.id == LaapDonationRequest.user_id)
        .order_by(LaapDonationRequest.created_at.desc())
    )
    if status_filter:
        q = q.where(LaapDonationRequest.status == status_filter)
    else:
        q = q.where(LaapDonationRequest.status != "withdrawn")
    result = await session.execute(q.offset(skip).limit(limit))
    out: list[LaapDonationResponse] = []
    for row, full_name in result.all():
        urls = await _photo_urls(session, ET_DONATION, row.id)
        out.append(
            LaapDonationResponse(
                id=row.id,
                user_id=row.user_id,
                creator_full_name=full_name,
                title=row.title,
                description=row.description,
                items_or_need_summary=row.items_or_need_summary,
                how_to_donate=row.how_to_donate,
                contact_phone=row.contact_phone,
                upi_id=row.upi_id,
                bank_account_hint=row.bank_account_hint,
                target_amount_inr=row.target_amount_inr,
                status=row.status,
                photo_urls=urls,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    return out


@router.get("/donations/{donation_id}", response_model=LaapDonationResponse)
async def get_donation_request(
    donation_id: uuid.UUID,
    session: SessionDep,
) -> LaapDonationResponse:
    result = await session.execute(
        select(LaapDonationRequest, User.full_name)
        .join(User, User.id == LaapDonationRequest.user_id)
        .where(LaapDonationRequest.id == donation_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Donation request not found")
    d, full_name = row
    urls = await _photo_urls(session, ET_DONATION, d.id)
    return LaapDonationResponse(
        id=d.id,
        user_id=d.user_id,
        creator_full_name=full_name,
        title=d.title,
        description=d.description,
        items_or_need_summary=d.items_or_need_summary,
        how_to_donate=d.how_to_donate,
        contact_phone=d.contact_phone,
        upi_id=d.upi_id,
        bank_account_hint=d.bank_account_hint,
        target_amount_inr=d.target_amount_inr,
        status=d.status,
        photo_urls=urls,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


@router.patch("/donations/{donation_id}", response_model=LaapDonationResponse)
async def update_donation_request(
    donation_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    body: LaapDonationUpdate,
) -> LaapDonationResponse:
    result = await session.execute(
        select(LaapDonationRequest).where(LaapDonationRequest.id == donation_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Donation request not found")
    if not _can_edit(current_user, row.user_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await session.flush()
    await session.refresh(row)

    u = await session.execute(select(User.full_name).where(User.id == row.user_id))
    creator = u.scalar_one()
    urls = await _photo_urls(session, ET_DONATION, row.id)
    return LaapDonationResponse(
        id=row.id,
        user_id=row.user_id,
        creator_full_name=creator,
        title=row.title,
        description=row.description,
        items_or_need_summary=row.items_or_need_summary,
        how_to_donate=row.how_to_donate,
        contact_phone=row.contact_phone,
        upi_id=row.upi_id,
        bank_account_hint=row.bank_account_hint,
        target_amount_inr=row.target_amount_inr,
        status=row.status,
        photo_urls=urls,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
