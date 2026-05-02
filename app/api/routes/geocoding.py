from fastapi import APIRouter

from app.schemas.distribution import (
    Coordinate,
    GeocodedAddress,
    GeocodeRequest,
    GeocodeResponse,
    OptimizedStop,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
)
from app.services.geocoding import geocoding_service
from app.services.route_optimizer import RoutePoint, optimize_route

router = APIRouter(tags=["geocoding & routing"])


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode_addresses(data: GeocodeRequest) -> GeocodeResponse:
    results = await geocoding_service.geocode_batch(data.addresses)
    return GeocodeResponse(
        results=[
            GeocodedAddress(
                address=r.address,
                latitude=r.latitude,
                longitude=r.longitude,
                display_name=r.display_name,
                success=r.success,
            )
            for r in results
        ]
    )


@router.post("/optimize-route", response_model=OptimizeRouteResponse)
async def optimize_route_endpoint(data: OptimizeRouteRequest) -> OptimizeRouteResponse:
    start = RoutePoint(
        latitude=data.start.latitude,
        longitude=data.start.longitude,
        label=data.start.label,
    )
    destinations = [
        RoutePoint(latitude=d.latitude, longitude=d.longitude, label=d.label)
        for d in data.destinations
    ]
    ordered, total_km = optimize_route(start, destinations)
    return OptimizeRouteResponse(
        ordered_stops=[
            OptimizedStop(
                order=s.order,
                latitude=s.point.latitude,
                longitude=s.point.longitude,
                label=s.point.label,
                distance_from_previous_km=s.distance_from_previous_km,
            )
            for s in ordered
        ],
        total_distance_km=total_km,
    )
