import math
from dataclasses import dataclass


@dataclass
class RoutePoint:
    latitude: float
    longitude: float
    label: str | None = None


@dataclass
class OptimizedStop:
    order: int
    point: RoutePoint
    distance_from_previous_km: float


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth in kilometres."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def optimize_route(
    start: RoutePoint, destinations: list[RoutePoint]
) -> tuple[list[OptimizedStop], float]:
    """
    Nearest-neighbour TSP heuristic.

    Returns the ordered list of stops (excluding start) and the total
    estimated distance in km.
    """
    if not destinations:
        return [], 0.0

    remaining = list(destinations)
    ordered: list[OptimizedStop] = []
    current = start
    total_distance = 0.0
    order = 1

    while remaining:
        best_idx = 0
        best_dist = haversine_km(
            current.latitude,
            current.longitude,
            remaining[0].latitude,
            remaining[0].longitude,
        )
        for i in range(1, len(remaining)):
            d = haversine_km(
                current.latitude,
                current.longitude,
                remaining[i].latitude,
                remaining[i].longitude,
            )
            if d < best_dist:
                best_dist = d
                best_idx = i

        nearest = remaining.pop(best_idx)
        total_distance += best_dist
        ordered.append(
            OptimizedStop(
                order=order,
                point=nearest,
                distance_from_previous_km=round(best_dist, 3),
            )
        )
        current = nearest
        order += 1

    return ordered, round(total_distance, 3)
