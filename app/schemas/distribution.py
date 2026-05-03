import datetime
import uuid

from pydantic import BaseModel, Field


class DistributionResponse(BaseModel):
    id: uuid.UUID
    drive_id: uuid.UUID | None = None
    name: str
    contact: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float
    longitude: float
    water_bowl_photo: str | None = None
    owner_photo: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class GeocodeRequest(BaseModel):
    addresses: list[str] = Field(..., min_length=1)


class GeocodedAddress(BaseModel):
    address: str
    latitude: float | None = None
    longitude: float | None = None
    display_name: str | None = None
    success: bool


class GeocodeResponse(BaseModel):
    results: list[GeocodedAddress]


class Coordinate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    label: str | None = None


class OptimizeRouteRequest(BaseModel):
    start: Coordinate
    destinations: list[Coordinate] = Field(..., min_length=1)


class OptimizedStop(BaseModel):
    order: int
    latitude: float
    longitude: float
    label: str | None = None
    distance_from_previous_km: float


class OptimizeRouteResponse(BaseModel):
    ordered_stops: list[OptimizedStop]
    total_distance_km: float


class StatsResponse(BaseModel):
    # Water bowl
    total_distributions: int
    total_drives: int
    drives_completed: int
    drives_planned: int
    unique_addresses: int
    # Rescue
    total_rescues: int = 0
    open_rescues: int = 0
    resolved_rescues: int = 0
    # Adoption
    total_adoptions: int = 0
    open_adoptions: int = 0
    fulfilled_adoptions: int = 0
    # Donations
    total_donations_inr: float = 0.0
    donation_count: int = 0
    # Volunteers
    total_volunteers: int = 0
    active_volunteers: int = 0
